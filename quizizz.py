'''
    Program: Quizizz Solver
    Version: 2.0
    Author : Meghraj Goswami
    Github : github.com/megz15/quizizz-solver
'''
#Imports - Selenium
from msedge.selenium_tools import Edge,EdgeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

#Imports - Misc
import sys,os,requests
from webbrowser import open as wb
from time import sleep

#Imports - Pysimplegui
import PySimpleGUI as sg
sg.theme('DarkBlack1')

#Functions
def resource_path(relative_path):                               #Make compatible with PyInstaller
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def waitForLoad(driver,term,timeout=50):                        #Wait for element to load
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, term)))

def parser(sti):                                                #Parse questions and answers from very messy JSON
    #Got most of code of this function from github.com/LQR471814/Quizizz-Hack, thank you :)
    quizInfo = (requests.get('https://quizizz.com/quiz/'+sti)).json()
    allAns = {}
    for question in quizInfo["data"]["quiz"]["info"]["questions"]:
        if question["type"] == "MCQ":
            #? Single answer
            if question["structure"]["options"][int(question["structure"]["answer"])]["text"] == "":
                #? Image answer
                answer = question["structure"]["options"][int(question["structure"]["answer"])]["media"][0]["url"]
            else:
                answer = question["structure"]["options"][int(question["structure"]["answer"])]["text"]
        elif question["type"] == "MSQ":
            #? Multiple answers
            answer = []
            for answerC in question["structure"]["answer"]:
                if question["structure"]["options"][int(answerC)]["text"] == "":
                    answer.append(question["structure"]["options"][int(answerC)]["media"][0]["url"])
                else:
                    answer.append(question["structure"]["options"][int(answerC)]["text"])

        questionStr = question["structure"]["query"]["text"].replace('<p>','').replace('</p>','')
        allAns[questionStr] = answer
    return allAns

#Set webdriver to Edge Chromium v86.0.622.56
options = EdgeOptions()
options.use_chromium = True                                     #Uses chromium-based edgium, remove to use legacy edge
options.add_experimental_option('w3c',False)                    #Bypass w3c performance logging restrictions
options.set_capability('loggingPrefs',{'performance':'ALL'})    #Enable capture Network headers
path = resource_path("res/msedgedriver.exe")

#GUI Window
menu_def = [['&Menu', ['&Clear All','&About','E&xit','---','Su&rprise']]]   #Menu-bar layout
layout = [[sg.Menu(menu_def,tearoff=False)],                                #GUI layout
         [sg.Text(' '*8),sg.Image(resource_path('res/qz.png'))],
         [sg.Text()],
         [sg.Text('Enter name: '),sg.InputText('Type name',size=(10,None),key='_NAME_')],
         [sg.Text('Enter code:  '),sg.InputText('Quiz code',size=(10,None),key='_CODE_')],
         [sg.Text()],
         [sg.Text(' '*8),sg.Button(image_filename=resource_path('res/b.png'),key='_QZ_',button_color=(sg.theme_background_color(),sg.theme_background_color()),border_width=0)]
         ]

window = sg.Window('Quizizz Solver',layout,font=('Helvetica', 14))          #Create PySimpleGUI Window instance

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED,'Exit'): #Close window
        break
    if event=='Clear All':              #Reset text fields
        window['_NAME_'].update('Type name')
        window['_CODE_'].update('Quiz code')
    if event=='About':                  #About Program
        sg.popup('Quizizz Solver 2.0:\nAutomatically solve Quizizz quizzes\n\nMade in Python 3.8.6 by Meghraj Goswami\n',title='About Program')
    if event=='Surprise':               #Free crypto
        wb('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    if event=='_QZ_':                   #Main logic
        driver = Edge(options=options,executable_path=path)
        driver.get('https://www.quizizz.com/join')
        
        waitForLoad(driver,'check-room-input')  #Wait for code input box and fill in 6-digit quiz code
        driver.find_element_by_class_name('check-room-input').send_keys(values['_CODE_'], Keys.RETURN)

        waitForLoad(driver,'enter-name-field')  #Wait for name input box and fill in entered name
        driver.find_element_by_class_name('enter-name-field').send_keys(values['_NAME_'], Keys.RETURN)

        waitForLoad(driver,'question-text')     #Wait for question appearance to capture quiz ID from Network headers
        for i in driver.get_log('performance'): #Get all Network headers
            i = str(i)
            if 'gameSummaryRec?quizId=' in i:   #Filter lot of text for game id
                quiz_id = i[i.find('gameSummaryRec?quizId=')+22:i.find('",":scheme":"https"')]
                break
        pars = parser(quiz_id)                  #Parse q's and a's and store in dictionary

        while True:                             #Select answers
            try:
                sleep(1)                        #Wait for question to load properly
                waitForLoad(driver,'question-text')
                b = pars[driver.find_element_by_class_name('question-text-color').text]                                         #Get answer for presented question
                choices = driver.find_element_by_css_selector('.options-container').find_elements_by_css_selector('.option')    #Get all presented answers
                for answer in choices:      #Loop through presented answers and select correct answer
                    c = answer.find_element_by_css_selector(".resizeable")
                    if c.get_attribute('innerHTML') == b:
                        c.click()           #Click on correct option element
                        sleep(4)            #Wait for next question to load properly
                        break               #Break out of loop if correct answer submitted
            except NoSuchElementException:  #All questions have been completed and while loop raises error
                sg.popup('Quiz Completed!')
                break
 
window.close()