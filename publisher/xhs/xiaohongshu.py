import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

import Config
import Cookie
import Init
import Create


def select_user():
    while Config.UserList:
        for i, v in enumerate(Config.UserList):
            print(f"{i + 1}.{v}", end="\t")
        phone_number = input("\n请选择用户(输入'n'使用手机号登录)：")
        if phone_number == 'n':
            # 手机号登录
            Config.login_status = True
            return
        try:
            Config.CurrentUser = Config.UserList[int(phone_number) - 1]
            return
        except (ValueError, IndexError):
            print("请输入正确的值！")


def login_successful():
    # 获取昵称
    name_content = WebDriverWait(Config.Browser, 10, 0.2).until(
        lambda x: x.find_element(By.CSS_SELECTOR, ".name-box")).text
    print(f"{name_content},登录成功!")
    Config.Browser.get("https://creator.xiaohongshu.com/publish/publish")
    Config.CurrentUser = name_content
    # 获取Cookie
    Cookie.get_new_cookie()
    Cookie.save_cookie()


def cookie_login():
    Cookie.set_cookie()
    try:
        WebDriverWait(Config.Browser, 10, 0.2).until(
            lambda x: x.find_element(By.CSS_SELECTOR, ".name-box")).text
    except TimeoutException:
        Config.login_status = True
        return
    login_successful()


def login():
    Config.Browser.get("https://creator.xiaohongshu.com/login")
    if not Config.login_status:
        cookie_login()
        return
    # 访问登陆页面
    while True:
        phone = input("请输入手机号：")
        if len(phone) == 11:
            break
        print("手机号码不合法！")

    xpath_phone_input = "/html/body/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[2]/div[1]/div[1]/input"
    xpath_code_sender = "/html/body/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/div[2]"

    xpath_code_input = "/html/body/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/input"
    Config.Browser.find_element(By.XPATH, xpath_phone_input).send_keys(phone)

    xpath_login_button = "/html/body/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/button"

    # 发送验证码
    Config.Browser.find_element(By.XPATH, xpath_code_sender).click()

    # 获取错误标签
    # error_span = 'return document.querySelector(".css-1qf7tqh").value'
    # error = Config.Browser.execute_script(error_span)
    # if error != "":
    #     print(error)
    #     return

    while True:
        # 输入验证码
        code = input("请输入验证码：")
        if len(code) == 6:
            break
        print("验证码不合法！")


    Config.Browser.find_element(By.XPATH, xpath_code_input).send_keys(code)
    # 登录
    Config.Browser.find_element(By.XPATH, xpath_login_button).click()
    login_successful()


def switch_users():
    print("正在清除Cookie")
    Config.Browser.delete_all_cookies()
    select_user()
    login()


def Quit():
    Cookie.save_cookie()
    print("Bye!")
    Config.Browser.quit()
    sys.exit(0)


def select_create():
    while True:
        if Config.Browser.current_url != "https://creator.xiaohongshu.com/publish/publish":
            Config.Browser.get("https://creator.xiaohongshu.com/publish/publish?from=menu")
        print("1. 视频上传  2.图文上传  3. 切换用户 4.退出")
        select = input("请选择功能：")
        match select:
            case '1':
                Create.create_video()
                return
            case '2':
                Create.create_image()
                return
            case '3':
                switch_users()
                return
            case '4':
                Quit()
                return
            case default:
                print("请输入合法的数字！")


def start():
    try:
        # 初始化程序
        print("正在初始化程序……")
        Init.init()
        # 选择用户
        select_user()
        # 登录
        login()
        while True:
            # 选择功能
            select_create()
    except KeyboardInterrupt:
        print("\nBye!")
    except Exception as e:
        print(f"发生了一些错误：\n{e}")
