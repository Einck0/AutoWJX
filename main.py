import inspect
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
import random
import time
import numpy as np
import logging
from scipy.stats import norm
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from typing import List, Tuple, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 题号和选项从0开始
url = "https://www.wjx.cn/vm/exjpFvn.aspx#"
count = 30  # 填写数量
num = 16  # 题目数量
ui = 0  # ui模式 1:有界面 0:无界面


ANSWER = {
    # 题号:[选项权重] 选项权重越大越容易被选中,权重个数需要等于选项个数，当选项权重为1个时，表示倾向于选择该选项
    # 当不包含某题时，表示随机选择，量表为一个题
    # 填空题格式：[30, ['答案1','答案2','答案3']]，如果为空则读取txt文件文件名为q{题号}.txt
    1: [30, 1],
    10: [60, 40],
    11: [1],
    12: [3],
    13: [10, 10, 10, 80, 20],
    14: [1, 1, 1],
    15: [],
}

ACTIONS_ON_BEFORE: List[Tuple[Callable, tuple, dict]] = []  # 保存填写前的函数
ACTIONS_ON_AFTER: List[Tuple[Callable, tuple, dict]] = []  # 保存填写后的函数


def read_text():
    for i in range(num):
        if ANSWER[i][0] != [] or i not in ANSWER:
            continue
        with open("q{}.txt".format(i), "r", encoding="UTF-8") as f:
            if not f.readable():
                return
            while True:
                line = f.readline().strip("\n")
                if not line:
                    break
                ANSWER[i][0].append(line)


def write_text(i):
    with open("q{}.txt".format(i), "w", encoding="utf-8") as f:
        for text in ANSWER[i][0]:
            f.write(text + "\n")


def answer_rondom():
    list_vals = np.linspace(1, 5, 5)
    # 计算每个数据点的正态分布概率密度
    w = norm.pdf(list_vals, 4, 0.5) * 3
    w += norm.pdf(list_vals, 5, 0.5) * 1.5
    w += norm.pdf(list_vals, 2, 1)

    return w


def close_ui(options):
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")


def weight_check(answ, length, i):
    if len(answ) == 1:
        list_vals = np.linspace(1, length, length)
        answ = norm.pdf(list_vals, answ[0], 1)
    elif len(answ) < length:
        logging.warning("第{}题选项权重个数小于选项个数".format(i + 1))
        list_vals = np.linspace(1, length, length)
        answ = norm.pdf(list_vals, length / 2, 1)
    return answ


def write(rank, i, answ):
    type_q = rank.get_attribute("type")

    # 单选
    if type_q == "3":
        radio_options = rank.find_elements(By.CLASS_NAME, "ui-radio")
        length = len(radio_options)
        answ = weight_check(answ, length, i)
        answer = random.choices(range(length), weights=answ, k=1)
        radio_options[answer[0]].click()

    # 多选
    elif type_q == "4":
        ui_check = rank.find_elements(By.CLASS_NAME, "label")
        switch = True
        length = len(ui_check)
        answ = weight_check(answ, length, i)
        while switch:
            for k in range(len(ui_check)):
                if random.randint(0, 100) <= answ[k]:
                    ui_check[k].click()
                    switch = False

    # 矩阵 量表
    elif type_q == "6":
        mat_data = rank.find_elements(By.CSS_SELECTOR, "tr[tp=d]")
        for s in range(len(mat_data)):
            single_mat_row = mat_data[s].find_elements(
                By.CLASS_NAME, "rate-off.rate-offlarge"
            )
            length = len(single_mat_row)
            answ = weight_check(answ, length, i)
            select = random.choices(range(length), weights=answ, k=1)
            single_mat_row[select[0]].click()

    elif type_q == "5":
        mat_data = rank.find_elements(By.CSS_SELECTOR, "ul[tp=d]")
        for s in range(len(mat_data)):
            single_mat_row = mat_data[s].find_elements(
                By.CLASS_NAME, "rate-off.rate-offlarge"
            )
            length = len(single_mat_row)
            answ = weight_check(answ, length, i)
            select = random.choices(range(length), weights=answ, k=1)
            single_mat_row[select[0]].click()

    # 填空
    elif type_q == "1":
        if answ == []:
            return
        if random.randint(0, 100) <= answ[0]:
            text_data = rank.find_element(By.ID, "q" + str(i + 1))
            if not len(answ[1]):
                logging.warning("第{}题无填写内容".format(i + 1))
                return
            text = answ[1][0]
            answ[1].pop(0)
            text_data.send_keys(text)
            write_text(i)


def edge_driver():
    options = Options()
    if ui != 1:
        close_ui(options)
    driver_path = "msedgedriver.exe"
    service = Service(executable_path=driver_path)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--ignore-certificate-error")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36"
    )
    options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Edge(options=options, service=service)


def auto_write():
    driver = edge_driver()
    driver.get(url)
    pages = driver.find_elements(By.CLASS_NAME, "fieldset")

    for page in pages:
        questions = page.find_elements(By.CLASS_NAME, "field.ui-field-contain")
        if len(questions) == 0:
            logging.warning("没有找到题目")
            return 1

        logging.info("开始填写问卷")
        for question in questions:
            q_num = int(question.get_attribute("topic"))
            if q_num not in ANSWER:
                ANSWER[q_num] = []
            try:
                write(question, q_num, ANSWER[q_num])
            except ElementNotInteractableException:
                logging.warning("第{}题无法填写".format(q_num))
                continue

            for func, args, kwargs in ACTIONS_ON_BEFORE:
                # 获取函数签名
                sig = inspect.signature(func)

                # 如果接收到的数据是特定的关键字参数
                if "q_num" in sig.parameters:
                    kwargs["q_num"] = q_num
                func(*args, **kwargs)

        divNext = driver.find_element(By.ID, "divNext")
        if divNext and divNext.is_displayed() and divNext.is_enabled():
            divNext.click()

    logging.info("填写完成")
    driver.execute_script(
        "Object.defineProperties(navigator,{webdriver:{get:()=>undefined}})"
    )
    time.sleep(random.randint(2, 5))
    for _ in range(3):
        try:
            driver.find_element(By.ID, "ctlNext").click()
            break
        except ElementNotInteractableException:
            time.sleep(0.5)

    for _ in range(10):
        time.sleep(0.5)
        if driver.current_url != url:
            driver.quit()
            return 0
    driver.quit()
    return 1


def add_action_after_write(func: Callable, args: tuple, kwargs: dict):
    ACTIONS_ON_AFTER.append(func, args, kwargs)


if __name__ == "__main__":
    w = answer_rondom()
    select = random.choices(range(1, 6), weights=w, k=1)
    for i in range(2, 10):
        temp = random.choices([-1, 0, 1], weights=[1, 4, 2], k=1)
        ANSWER[i] = [min(max(select[0] + temp[0], 1), 5)]

    for i in range(count):
        random.seed(time.time())
        backup_ANSWER = ANSWER.copy()
        logging.info("正在填写第{}份问卷（共{}份）".format(i + 1, count))
        j = 0
        while j < 4:  # 重试次数
            ANSWER = backup_ANSWER.copy()
            if not auto_write():
                logging.info("第{}份问卷已经提交（共{}份）".format(i + 1, count))
                break
            logging.warning("第{}份问卷提交失败（第{}次尝试）".format(i + 1, j + 1))
            j += 1
            time.sleep(3)
        if j == 4:
            exit(0)
