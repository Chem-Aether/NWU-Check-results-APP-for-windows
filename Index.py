import binascii
from bs4 import BeautifulSoup
import rsa
import json
import requests
import re
import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5 import uic

def get_json():
    with open('config.json', 'r') as f:
        config_json = json.load(f)
    f.close
    with open('option_encoded.json') as f:
        encoded_json = json.load(f)
    return config_json,encoded_json

class Login():
    def  __init__(self,JSON):
        self.modules = None
        self.token = None
        self.pub = None
        self.header = None
        self.cookie = None
        self.request = None

        self.name = JSON['name']
        self.password = JSON['password']
        self.temp_password = self.password

        self.url = JSON['url']
        self.PublicKey = JSON['PublicKey']

        self.time = int(time.time())
        self.sessions = requests.Session()


    # 获取公钥密码
    def get_public_key(self):

        result = self.sessions.get(self.PublicKey + str(self.time)).json()
        self.modules = result["modulus"]
        #print(self.modules)

    # 获取CsrfToken
    def get_csrf_token(self):
        r = self.sessions.get(self.url+ str(self.time))
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        self.token = soup.find('input', attrs={'id': 'csrftoken'}).attrs['value']
        #print(self.token)

    # 加密密码
    def process_public(self):
        weibo_rsa_e = 65537
        self.password = self.temp_password
        message = str(self.password).encode()

        rsa_n = binascii.b2a_hex(binascii.a2b_base64(self.modules))
        key = rsa.PublicKey(int(rsa_n, 16), weibo_rsa_e)
        encropy_pwd = rsa.encrypt(message, key)
        self.password = binascii.b2a_base64(encropy_pwd)
        #print(self.password)

    # 登录函数
    def login(self):
        self.get_public_key()
        self.get_csrf_token()
        self.process_public()

        try:
            self.header = {
                'Accept': 'text/html, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0',
                'Connection': 'keep-alive',
                'Referer': self.url + str(self.time),
                'Upgrade-Insecure-Requests': '1',
            }
            data = {
                'csrftoken': self.token,
                'mm': self.password,
                'mm': self.password,
                'yhm': self.name
            }
            self.request = self.sessions.post(self.url, headers=self.header, data=data)
            self.cookie = self.request.request.headers['cookie']
            key_word = r'用户名或密码不正确'
            if re.findall(key_word, self.request.text):
                print('用户名或密码错误,请查验..')
                return False
                #sys.exit()
            else:
                print("登陆成功")
                return True
        except Exception as e:
            print(str(e))
            #sys.exit()


class Seek():
    def __init__(self,config_json,encoded_json):
        #登陆教务处
        self.logined = Login(config_json)
        self.logined.login()


        self.encoded_json = encoded_json
        self.xnm = config_json['TestResult_year']
        self.xqm = config_json['TestResult_term']

        #Login.login(config_json)

    #获取个人信息
    def get_PersonalInformation(self):
        url = self.encoded_json['PersonalInformation']+self.logined.name
        req = self.logined.sessions.get(url=url, headers=self.logined.header)
        print(req.text)
        print('')

    #获取课程表
    def get_ClassScheduleCard(self):
        data = {
            'xnm':config_json['ClassScheduleCard_year'],
            'xqm':config_json['ClassScheduleCard_term']
        }
        url = self.encoded_json['ClassScheduleCard']+self.logined.name
        req = self.logined.sessions.post(url = url, headers=self.logined.header, data=data)
        kbList = json.loads(req.text)['kbList']
        ClassScheduleList = []
        for each in kbList:
            ClassName = each['kcmc']
            ClassTime = each['jc']
            ClassRoom = each['cdmc']
            WeekDay = each['xqjmc']
            Teacher = each['xm']
            WeekDayNum = each['xqj']
            #print(f'{ClassName} {ClassTime} {ClassRoom} {WeekDay} {WeekDayNum} {Teacher}')
            ClassScheduleList.append([ClassName,ClassTime,ClassRoom,WeekDay,WeekDayNum,Teacher])
        print(ClassScheduleList)
        return ClassScheduleList

    #查询成绩
    def get_TestResult(self):
        data = {
            'xnm': self.xnm,
            'xqm': self.xqm,
            'queryModel.showCount':'100',
            'queryModel.currentPage':'1'
        }
        url = self.encoded_json['TestResult']+self.logined.name
        req = self.logined.sessions.post(url=url, headers=self.logined.header, data=data)
        items = json.loads(req.text)['items']
        TestResultList = []
        for each in items:
            ClassName = each['kcmc']#科目
            HundredthResult = each['bfzcj']#成绩
            Credit = each['jd']#绩点
            try:
                ClassAttribute = each['kclbmc']#课程属性
            except:
                ClassAttribute = ''
            TestAttribute= each['ksxz']#成绩属性
            TestResultList.append([ClassName,HundredthResult,Credit,ClassAttribute,TestAttribute])

            print(f'{ClassName} {HundredthResult} {Credit} {ClassAttribute} {TestAttribute}')
        return TestResultList

    #查考试信息
    def get_TestMeaasge(self):
        data = {
            'xnm': self.xnm,
            'xqm': self.xqm,
            'queryModel.showCount':'100',
            'queryModel.currentPage':'1'
        }
        url = self.encoded_json['TestMeaasge']+self.logined.name
        req = self.logined.sessions.post(url=url, headers=self.logined.header, data=data)
        items = json.loads(req.text)['items']
        for each in items:
            TestRoom = each['cdmc']
            TestForm = each['ksfs']
            TestTime = each['kssj']
            TestName = each['kcmc']

            print(f'{TestName} {TestRoom} {TestTime} {TestForm } ')


    #查重修成绩
    def get_RemarkResult(self):
        data = {
            'cxxnm': '2022',
            'cxxqm': '3',
            'queryModel.showCount': '5000'
        }
        url = self.encoded_json['RemarkResult']+self.logined.name
        req = self.logined.sessions.post(url=url, headers=self.logined.header, data=data)
        items = json.loads(req.text)['items']
        RemarkResultList = []
        for each in items:
            try:
                TestName = each['kcmc'].split('<')[0]
                TestReslut = each['cj']
                TestGradePoint = each['jd']
                print(f'{TestName} {TestReslut} {TestGradePoint } ')
                RemarkResultList.append([TestName,TestReslut,TestGradePoint])
            except:pass

        data['cxxqm'] = '12'
        url = self.encoded_json['RemarkResult']+self.logined.name
        req = self.logined.sessions.post(url=url, headers=self.logined.header, data=data)
        items = json.loads(req.text)['items']
        for each in items:
            try:
                TestName = each['kcmc'].split('<')[0]
                TestReslut = each['cj']
                TestGradePoint = each['jd']
                print(f'{TestName} {TestReslut} {TestGradePoint } ')
                RemarkResultList.append([TestName,TestReslut,TestGradePoint])
            except:pass
        return RemarkResultList


class Windows():
    def __init__(self,JSON):
        self.config = JSON
        super().__init__()
        self.InitLoadUI()

        self.UI = None
        self.seek = None




    def InitLoadUI(self):
        self.LoadUi = uic.loadUi("LOAD.ui")

        self.LoadUi.BUTTON.clicked.connect(self.Get_load)
        self.LoadUi.RELOAD.clicked.connect(self.ReLoad)
        self.LoadUi.show()

    def InitUI(self):
        self.UI = uic.loadUi("UI0.ui")

        self.UI.TestResult.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.UI.TestResult.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.seek = Seek(config_json=config_json, encoded_json=encoded_json)


        self.FillTab(DataList = self.seek.get_RemarkResult() , Table = self.UI.TestResult)

        #self.FillTab(DataList = self.seek.get_ClassScheduleCard(), Table = self.UI.ClassScheduleCard)

    def Get_load(self):
        self.config['name'] = self.LoadUi.NAME.text()
        self.config['password'] = self.LoadUi.PASSWORD.text()
        BOX = self.LoadUi.CHECKBOX.isChecked()
        print(self.LoadUi.NAME.text(), self.LoadUi.PASSWORD.text(), BOX)

        #登陆成功且选择写入
        LOADTest = Login(self.config)
        if LOADTest.login():
            if BOX:
                print("TRUE")
                with open("config.json", 'w') as f:
                    json.dump(self.config, f, ensure_ascii=False)

            self.Change(self.LoadUi,self.UI)
        else:
            self.LoadUi.NAME.setText("")
            self.LoadUi.PASSWORD.setText("")
        #self.LoadUi.hide()

    def ReLoad(self):
        LOADTest = Login(self.config).login()
        if LOADTest:
            print("成功")
            self.Change(self.LoadUi, self.UI)
        else:
            print("失败")

    def ChangeWindows(self,Windows1,Windows2):
        Windows1.hide()
        Windows2.show()
        #time.sleep(1000)

    def Change(self,Windows1,Windows2):
        self.InitUI()
        time.sleep(10)
        Windows1.hide()
        self.UI.show()

    def FillTab(self,DataList,Table):
        #TestResult = self.seek.get_TestResult()
        Table.setRowCount(len(DataList))
        for i in range(0,len(DataList)):
            for j in range(0,len(DataList[i])):
                Table.setItem(i,j,QTableWidgetItem(str(DataList[i][j])))



if __name__ == '__main__':
    config_json,encoded_json = get_json()

    #login = Login(config_json)
    #login.login()

    #seek = Seek(config_json=config_json,encoded_json=encoded_json)

    #seek.get_PersonalInformation()

    #seek.get_ClassScheduleCard()
    #seek.get_TestMeaasge()
    #seek.get_TestResult()

    app = QApplication(sys.argv)


    windows = Windows(config_json)

    sys.exit(app.exec_())

