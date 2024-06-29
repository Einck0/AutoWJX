
from selenium import webdriver
import random
import time
import numpy as np
from scipy.stats import norm
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
#题号和选项从0开始
url='https://www.wjx.cn/vm/epPFYfH.aspx#'
count=50
num=3
ui=1    #ui模式 0:有界面 1:无界面
ANSWER={
    #题号:[选项权重] 选项权重越大越容易被选中,权重个数需要等于选项个数
    #必须包含每个题目序号，量表为一个题
    #填空题格式：[['答案1','答案2','答案3‘],30]，如果为空则读取txt文件文件名为q{题号}.txt
    0:[3],
    1:[3],
    2:[3]
}
def read_text():
    for i in range(num):
        if ANSWER[i][0] != [] or i not in ANSWER:
            continue
        with open('q{}.txt'.format(i),'r',encoding='UTF-8') as f:
            if not f.readable():
                return
            while True:
                line = f.readline().strip('\n')
                if not line:
                    break
                ANSWER[i][0].append(line)
def write_text(i):
    with open('q{}.txt'.format(i),'w',encoding='utf-8') as f:
        for text in ANSWER[i][0]:
                f.write(text+'\n')                
def answer_rondom():
    list = np.linspace(1, 5, 5) 
    # 计算每个数据点的正态分布概率密度
    w = norm.pdf(list, 4, 0.5)*3
    w += norm.pdf(list, 5, 0.5)*1.5
    w+= norm.pdf(list, 2, 1)

    return w


time_start = time.time()
class Time:#计算时间
        @staticmethod 
        def now():  
            now_time=time.time()
            dec = now_time - time_start
            minute_temp = int(dec / 60)
            second_temp = dec % 60
            return minute_temp,second_temp

def close_ui(options):
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')

def write(rank,i,ANSWER):
    type_q = rank.get_attribute("type")
        # 单选
    if(type_q == '3'):
        check = rank.find_elements(By.CLASS_NAME,"ui-radio")
        length = len(check)
        if len(ANSWER) == 1:
            # 生成数据点
            list = np.linspace(1, length, length) 
            # 计算每个数据点的正态分布概率密度
            ANSWER = norm.pdf(list, ANSWER, 1)
        elif len(ANSWER) < length:
            print("%02d:%02d" % (Time.now()),"第{}题选项权重个数小于选项个数".format(i+1))
            # 生成数据点
            list = np.linspace(1, length, length) 
            # 计算每个数据点的正态分布概率密度
            ANSWER = norm.pdf(list, length/2, 1)
        answer=random.choices(range(length),weights=ANSWER,k=1)
        check[answer[0]].click()
    #     多选
    elif(type_q == '4'):
        ui_check = rank.find_elements(By.CLASS_NAME,"label")
        switch = 1
        while switch:
            for k in range(len(ui_check)):
                if random.randint(0,100) <= ANSWER[k]:
                    ui_check[k].click()
                    switch = 0
    #     矩阵 量表
    elif(type_q == '6'):
        # print(rank.text)
        mat_data = rank.find_elements(By.CSS_SELECTOR,"tr[tp=d]")
        # mat_data = rank[i].find_elements_by_xpath("./tbody/tr[@tp=\"d\"]")
        
        for s in range(0,len(mat_data)):
            single_mat_row = mat_data[s].find_elements(By.CLASS_NAME,'rate-off.rate-offlarge')
            # print(len(single_mat_row))
            length = len(single_mat_row)
            # 生成数据点
            list = np.linspace(1, length, length) 
            # 计算每个数据点的正态分布概率密度
            w = norm.pdf(list, ANSWER, 0.6)
            select=random.choices(range(length),weights=w,k=1)
            single_mat_row[select[0]].click()
     #     填空
    elif(type_q == '1'):
        if random.randint(0,100) <= ANSWER[1]:
            text_data = rank.find_element(By.ID,"q"+str(i+1))
            if not len(ANSWER[0]):
                print("%02d:%02d" % (Time.now()),"第{}题无填写内容".format(i+1))
                return
            #text = random.choice(text_dict[i+1])
            text=ANSWER[0][0]
            ANSWER[0].pop(0)
            text_data.send_keys(text)
            write_text(i)
    
def auto_write(ui_mode=1):#自动填写问卷 0:有界面 1:无界面(默认)
    # 防止被浏览器识别为脚本
    # browser = webdriver.Chrome()
    # browser.get("https://www.wjx.cn/vm/YsK8J1l.aspx")
    
    options = Options()
    if ui_mode == 1:
        close_ui(options)
    driver_path='msedgedriver.exe'
    service=Service(executable_path=driver_path)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument("--ignore-certificate-error")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument( 'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36')
    #
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Edge(options=options,service=service)
    driver.get(url)
    # 获取到所有题目的选项
    rank = driver.find_elements(By.CLASS_NAME,'field.ui-field-contain')
    if len(rank) == 0:
        print("%02d:%02d" % (Time.now()),"没有找到题目")
        return 1
    
    print("%02d:%02d" % (Time.now()),"开始填写问卷")
    for i in range(num):
        if i not in ANSWER:
            ANSWER[i]=[]
        write(rank[i],i,ANSWER[i])
        i+=1

    print("%02d:%02d" % (Time.now()),"填写完成")

    #过人机验证
    driver.execute_script("Object.defineProperties(navigator,{webdriver:{get:()=>undefined}})")
    time.sleep(random.randint(2,5))
    #提交
    driver.find_element(By.ID,"ctlNext").click()
    for i in range(10):
        time.sleep(0.5)
        if driver.current_url!=url:
            driver.quit()
            return 0
    driver.quit()
    return 1
    

if __name__ == '__main__':
    # read_text()
    w=answer_rondom()
    select=random.choices(range(1,6),weights=w,k=1)
    for i in range(num):
        temp = random.choices([-1,0,1],weights=[1,4,2],k=1)
        ANSWER[i]=min(max(select[0]+ temp[0],5),1)

    for i in range(0,count):
        random.seed(time.time())
        backup_ANSWER=ANSWER.copy()
        print("%02d:%02d" % (Time.now()),"正在填写第{}份问卷（共{}份）".format(i+1,count))
        j=0
        while j < 4:
            ANSWER=backup_ANSWER.copy()
            if not auto_write(ui):
                print("%02d:%02d" % (Time.now()),"第{}份问卷已经提交（共{}份）\n\n".format(i+1,count))
                break
            print("%02d:%02d" % (Time.now()),"第{}份问卷提交失败（第{}次尝试）\n\n".format(i+1,j+1))
            j+=1
            time.sleep(3)
        if j == 4:
            exit(0)
