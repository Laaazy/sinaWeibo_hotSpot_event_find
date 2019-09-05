import numpy as np


# 转化数据形式，将同一天的博文放到一起
# 参数：每日每条微博一行的数据格式文件路径file,代表history_blogfile或者current_blogfile
# 返回：二维列表res，格式为每行为一天的微博[['','',...],[],...]
def transform_data(file):
    with open(file, encoding='utf-8') as f:
        res = []
        blog_oneday = []
        flag = 1
        date_now = ''

        for line in f:
            tmp = []
            attributes = line.strip('\n').split(',')
            date = attributes[0]  # 博文日期
            blog = attributes[2]  # 博文内容
            if flag == 1:
                date_now = date
                blog_oneday.append(blog)
                flag = 0
                continue
            if date == date_now:
                blog_oneday.append(blog)
            if date != date_now:
                tmp.extend(blog_oneday)
                res.append(tmp)
                date_now = date
                blog_oneday.clear()
                blog_oneday.append(blog)
        res.append(blog_oneday)
        return res


##  生成词汇表
#   参数: history_blogfile, current_blogfile 列表类型
#   返回: 词汇表(字典结构,value默认为0)
def genVocab(history_blogfile,current_blogfile):
    vocab_dic={}

    for blog_oneday in history_blogfile:
        for blog in blog_oneday:
            for word in blog.strip('\n').split():
                vocab_dic.setdefault(word,0)

    for blog_oneday in current_blogfile:
        for blog in blog_oneday:
            for word in blog.strip('\n').split():
                vocab_dic.setdefault(word,0)

    return vocab_dic


#计算blog_oneday当天词频
#参数：blog_oneday，一维列表,每个元素为一条微博的字符串
#返回：word_today字典类型，键为词，值为词频，词频为词次数除以总次数
def calculate_blog_oneday(blog_oneday):
    word_today={}
    total=0
    for blog in blog_oneday:
        for word in blog.strip('\n').split():
            word_today.setdefault(word,0)
            word_today[word]+=1
            total+=1
    for word in word_today:
        word_today[word]/=total
    return word_today


# 迭代计算fb
# 在vocab_dic中保存当前的fb
# input: vocab_dic, frequency都是dictionary类型
def cal_words_fb(vocab_dic, frequency):
    lambda_const = 0.996
    for word in frequency:
        vocab_dic[word] = lambda_const * vocab_dic[word] + (1 - lambda_const) * frequency[word]
    return vocab_dic


#计算词语对应的WS
#参数：词表，今日词频
#返回：WS，字典类型
def cal_words_WS(vocab_dic, frequency):
    WS = {}
    for word in frequency:
        WS.setdefault(word, 0)
        if vocab_dic[word]:
            WS[word] = frequency[word] / float(vocab_dic[word])
        else:
            WS[word] = 1

    return WS


# 对WS(w)进行箱线图分析得到 w和alpha
# 参数：WS字典
# 返回：w和alpha
def cal_w_and_alpha(WS):
    #第一四分位数，中位数，第三四分位数
    q1=q2=q3=0

    #按照value排序
    WS = sorted(WS.items(), key=lambda d: d[1], reverse=True)

    #计算第一四分位数，中位数，第三四分位数
    # len=len(WS)
    # count=0
    # for word in WS:
    #     count+=1
    #     if count==math.ceil(len/4):
    #         q1 = word[1]
    #     if count == math.ceil(len / 2):
    #         q2 = word[1]
    #     if count== math.ceil(len//4*3):
    #         q3 = word[1]
    #         break

    nums=[]
    for word in WS:
        nums.append(word[1])
    res=np.percentile(nums,(25,50,75),interpolation='midpoint')

    #计算w和alpha
    # w=q3+1.5*(q1-q3)
    w=res[2]+1.5*(res[2]-res[0])
    alpha=2*w
    return w,alpha


##  生成某天微博的主要词
#   参数:  frequency, WS都是字典，alpha是float
#   返回: 主要词表 (list)
def detectPrimaryWord(frequency, WS, alpha):
    primary_words_dict = {}# 主要词候选集合
    primary_words_list = []# 主要词集合
    for word in frequency:
        if WS[word] >= alpha:
            primary_words_dict.setdefault(word, frequency[word])
    sort_primary_words_dict = sorted(primary_words_dict.items(), key=lambda d: d[1], reverse=True)
    length = len(sort_primary_words_dict) * 0.001
    count = 0
    for word in sort_primary_words_dict:
        count+=1
        if count >= length:
            break
        primary_words_list.append(word)

    return primary_words_list


# 生成某天微博中，某个主要词对应的语境词
# 参数：当天词频frequency，WS，阈值w，主要词列表primary_words,今日微博blog_oneday
# 返回：docList[[主要词1,(语境词1,概率),(语境词2,概率),..], ...]
def detectContextWord(frequency,WS,w,primary_words,blog_oneday):
    context_words_list = []  # 语境词候选集合
    docList=[]
    tmp=[] # 包含某个主要词的今日微博集合
    sort_dic = {} # 用于对语境词的pdw排序，只取前10个pdw

    for word in frequency:
        if WS[word] >= w:
            context_words_list.append(word)
    for pWord in primary_words:
        #[主要词,(语境词1，条件概率1),...]
        doc=[]
        doc.append((pWord[0],1.00))

        tmp.clear()
        #取包含该主要词的今日微博,存入tmp
        for blog in blog_oneday:
            for word in blog.strip('\n').split():
                if word==pWord[0]:
                    tmp.append(blog)
                    break

        #遍历语境词候选集合，计算每个候选语境词在该集合中出现的条件概率
        for contextWord in context_words_list:
            count=0
            #计算语境候选词在包含该主要词的今日微博中出现的次数
            for blog in tmp:
                for word in blog.strip('\n').split():
                    if word == contextWord:
                        count+=1
            # 该主要词对应的该语境候选词出现的条件概率
            pdw=count/len(tmp)
            sort_dic[contextWord]=pdw
        res = sorted(sort_dic.items(), key=lambda d: d[1], reverse=True)
        count = 0
        for i in res:
            count += 1
            if count == 11:
                break
            if i[0] == pWord[0]:
                continue
            doc.append((i[0],i[1]))
        docList.append(doc)
    return docList



def genSensitiveWord(history_blogfile, current_blogfile):
    # 1. 生成词表
    vocab_dic = genVocab(history_blogfile, current_blogfile)

    # 2. 在词表里生成历史数据频率
    for blog_oneday in history_blogfile:
        # 计算 blog_oneday 当天词频
        frequency=calculate_blog_oneday(blog_oneday)
        # 迭代 vocab_dic 的基础词频(lambda)
        vocab_dic=cal_words_fb(vocab_dic,frequency)

    # 3. 根据current_blogfile每一天的微博生成主要词和语境词
    finalDoc=[]
    for blog_oneday in current_blogfile:
        # 计算 blog_oneday 当天词频
        frequency = calculate_blog_oneday(blog_oneday)
        WS=cal_words_WS(vocab_dic,frequency)
        # 对WS(w)进行箱线图分析得到 w和alpha
        w,alpha=cal_w_and_alpha(WS)
        # 得到主要词列表
        primary_words=detectPrimaryWord(frequency,WS,alpha)
        # 得到语境词
        docList=detectContextWord(frequency,WS,w,primary_words,blog_oneday)
        for i in docList:
            finalDoc.append(i)

	    # 依据当天词频迭代更新 vocab_dic 的基础词频(lambda)
        vocab_dic=cal_words_fb(vocab_dic,frequency)

    return finalDoc


current_blogfile = transform_data('./test_data/3.20current/current_blogfile.txt')
history_blogfile = transform_data('./test_data/3.20current/history_blogfile.txt')
finalDoc= genSensitiveWord(history_blogfile,current_blogfile)
print("共"+str(len(finalDoc))+"条文档")
for i in range(len(finalDoc)):
    print("第"+str(i+1)+"条文档:"+str(finalDoc[i]))
# print(finalDoc)
