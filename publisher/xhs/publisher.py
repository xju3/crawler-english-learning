import json
import os
import sys
import time
import shutil

from common.env import Environment
from db.opus_manager import OpusManager, OpusStatus
from publisher.xhs.cmd import list_dir_files
from publisher.xhs.web_interaction import WebInteraction

env = Environment()


class Publisher(object):

    def __init__(self):
        self.has_cookie = False
        self.user_list = []
        self.cookie_dict = {}
        self.web_interaction = WebInteraction()
        self.curr_user = ''
        self.load_cookie_users()
        self.opus_manager = OpusManager()

    def load_cookie_users(self):
        cookie_file = f'{env.config.cookie_file_name}'
        if os.path.isfile(cookie_file):
            with open(env.config.cookie_file_name, "r+", encoding="utf-8") as f:
                content = f.read()
                if content:
                    self.cookie_dict.update(json.loads(content))
                    self.has_cookie = True
        else:
            env.logger.error("cookie file not exist")
            return

        for k, _ in self.cookie_dict.items():
            self.user_list.append(k)
        env.logger.debug("user count: " + str(len(self.user_list)))

    def login_by_cookie(self):
        cookie = self.cookie_dict[env.config.xhs_phone]
        max_expiry_time= 0;
        for cookie in json.loads(cookie):
            env.driver.add_cookie(cookie)
            expiry = cookie['expiry']
            max_expiry_time = max(max_expiry_time, expiry)
        now = int(time.time())
        if now > max_expiry_time:
            self.login_by_phone()
        else:
            self.curr_user = self.web_interaction.get_text_by_css('.name-box')
            self.login_successfully(1)


    def login_by_phone(self):
        self.web_interaction.send_sms_code(env.config.xhs_phone)
        sms_code_valid = False
        while True:
            code = input("please enter sms code here：")
            if len(code) == 6:
                sms_code_valid = True
                break

        if sms_code_valid:
            self.web_interaction.phone_login(code)
            self.login_successfully(2)
        else:
            env.logger.error("sms code not valid")
            sys.exit(0)

    def run(self):
        # open browser
        self.web_interaction.open(env.config.xhs_login_url, env.config.xpath_login_button)
        # if there are cookies at local, login by cookie*
        if self.has_cookie:
            self.login_by_cookie()
        else:
            self.login_by_phone()

    def login_successfully(self, index):
        # 获取昵称
        time.sleep(env.config.sleep_medium_time)
        if index == 2:
            cookies = json.dumps(env.driver.get_cookies())
            self.cookie_dict[env.config.xhs_phone] = cookies
            with open(env.config.cookie_file_name, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.cookie_dict))
            env.logger.debug('cookie saved to file')
        env.logger.debug(f'{self.curr_user} login successfully')
        self.web_interaction.open(env.config.xhs_publish_url, env.config.xpath_start_publishing)
        self.publish()

    def publish(self):
        time.sleep(env.config.sleep_short_time)
        items = self.opus_manager.get_items_for_publishing(1)
        if len(items) == 0:
            env.logger.error("no data to publish")
            sys.exit(0)
        env.logger.debug(f"{list(map(lambda d: d.code, items)) }")
        self.web_interaction.start_publishing()
        for item in items:
            try:
                path = f'{env.config.opus_dir}/{item.code}'
                if not os.path.exists(path):
                    env.logger.error("directory not exist!")
                    self.opus_manager.set_opus_status(item.code, OpusStatus.no_pics)
                    continue

                pics = list_dir_files(path, 'jpg')
                if len(pics) == 0:
                    self.opus_manager.set_opus_status(item.code, OpusStatus.no_pics)
                    env.logger.error("no pics!")
                    continue
                self.web_interaction.publish_pictures(item, pics)
                time.sleep(env.config.sleep_medium_time)
                self.opus_manager.set_opus_status(item.code, OpusStatus.published)
                shutil.rmtree(f'{env.config.opus_dir}/{item.code}')
            except Exception as e:
                env.logger.error(e)
        env.driver.quit()


    def upload_video(self, file):
        self.web_interaction.open(env.config.xhs_publish_url)
        self.web_interaction.publish_video(file)
