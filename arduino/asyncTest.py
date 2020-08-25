# 모듈포함
import os, sys, signal, time
import requests, json

# 초기 세팅
SERIAL_NUMBER = '20200814042555141'

# 데이터 요청 Domain 선언
URL = 'http://localhost:80'

# 전역 변수 선언
sensings = {} # 센싱된 데이터가 키와 값으로 저장될 딕셔너리
received_keys = set()
basic_keys = {'success', 'sensed_position', 'sold_position', 'state'} # 라즈베리파이가 가공할 변수명 집합

# 서버에서 전달받은 음료 정보가 저장될 전역 변수
drinks = {
    'position' : [],
    'name' : [],
    'price' : [],
}

test = [
    [["success", "1"], ["sensed_position", "1"], ["sold_position", "-1"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "2"], ["sold_position", "-1"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "-1"], ["sold_position", "2"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "4"], ["sold_position", "3"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "5"], ["sold_position", "-1"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "6"], ["sold_position", "-1"], ["state", "0"]],
    [["success", "1"], ["sensed_position", "7"], ["sold_position", "-1"], ["state", "0"]]
] 

test2 = [["success", "0"]]

# 메인 함수
def main():
    # 음료수 정보 요청
    requestDrinks()
    pid = 0

    # 무한 반복
    # while True:
    for t in test :
        for data in t :
            receive = testReceive(data)

            # 이용 가능한 데이터라면 실행 
            if receive :
                # 수신한 변수명 저장 
                received_keys.add(receive[0])

                # 아두이노에서 받은 데이터를 변수명과 값의 형태로 저장, 딕셔너리 형태
                sensings[ receive[0] ] = int(receive[1])
                print(sensings)

                # 라즈베리파이가 가공할 데이터를 모두 수신 했다면 실행 
                if basic_keys.difference(received_keys) == set() :
                    # 아두이노에서 센싱된 데이터가 있으면 실행 
                    if sensings["success"] :
                        # 출력
                        print("센싱 데이터 수신 성공")
                        
                        # 판매된 음료수가 있을 경우에 실행
                        if sensings["sold_position"] != -1 :
                            print("판매된 음료 차감 데이터를 요청하고 스피커 출력을 실행합니다.")
                            # 판매된 음료수 정보 차감 요청
                            requestDrinksUpdate()
                            
                            # 실행중인 espeak 프로세스 종료
                            speak_exit(pid)

                            # 프로세스 생성
                            pid = os.fork()
                            if pid == 0 :
                                # 자식프로세스 실행 구문
                                print("스피커 출력을 실행합니다.")
                                speak("-v ko+f3 -s 160 -p 95", "sold", sensings["sold_position"]-1)
                                # 스피커 출력 후 프로세스 종료
                                sys.exit(0)
                            
                            time.sleep(2)
                            
                                    
                        # 손이 음료 버튼에 위치했을 경우에 실행
                        elif sensings["sensed_position"] != -1 :
                            # 실행중인 espeak 프로세스 종료
                            speak_exit(pid)

                            # 프로세스 생성
                            pid = os.fork()
                            if pid == 0 :
                                # 자식프로세스 실행 구문
                                print("물체가 감지되어 스피커 출력을 실행합니다.")
                                speak("-v ko+f3 -s 160 -p 95", "position", sensings["sensed_position"]-1)
                                # 스피커 출력 후 프로세스 종료
                                sys.exit(0)

                            time.sleep(2)
                                
                        # 수신한 변수명 집합 비우기 => 다음 센싱 때에도 정상 수신하는지 검사하기 위함 
                        received_keys.clear()
                            
                # 아두이노에서 False만 보냈을 경우 
                elif received_keys == {"success"} :
                    # 아두이노에서 센싱된 데이터가 없으면 실행
                    if not sensings["success"] :
                        print("센싱 데이터가 없습니다.\n서버로부터 음료 정보를 불러옵니다.")

                        # 음료수 정보 요청
                        requestDrinks()
                        
                        print("스피커 출력을 실행합니다. :인사말 ")
                        #speak("-v ko+f3 -s 160 -p 95", "basic")
            else :
                print("수신 가능한 센싱 데이터가 아닙니다.")

def speak_exit(pid) :
    if pid :
        # 자식프로세스 출력 후 종료
        print(pid, "espeak 프로세스를 종료합니다.")
        # os.kill(q_receive, signal.SIGTERM)
        # os.system("taskkill /F /pid {}".format(q_receive))
        # os.system("kill -9 {}".format(pid))
        os.system("killall -9 espeak")

def testReceive(data) :
    if data[0] in basic_keys :
        return data
    return False

# 음료수 정보 요청 함수 
def requestDrinks() :
    # 서버에게 요청할 데이터 생성
    drink = {
        'serial_number' : SERIAL_NUMBER, #if you pull server, then serialNumber -> serial_number
    }

    # 서버 요청

    response = requests.post(URL + '/rasp/drink/read', data = drink)
    # 응답 JSON 데이터 변환
    response = json.loads(response.text)

    # 서버에서 정상 응답이 온 경우
    if response["success"] == True :
        # 전역 변수 초기화
        del drinks["position"][:]
        del drinks["name"][:]
        del drinks["price"][:]

        # 서버 데이터 삽입
        for drink in response["drinks"] :
            drinks["position"].append(drink["position"])
            drinks["name"].append(drink["name"])
            drinks["price"].append(drink["price"])
        
    else :
        # 서버 에러 메세지 출력
        print(response["msg"])


# 판매된 음료수 정보 차감 요청 함수
def requestDrinksUpdate() :
    # 서버에게 요청할 데이터 생성
    drink = {
        'serial_number' : SERIAL_NUMBER,  
        'sold_position' : 1
        }
                            
    print('sensings : ', sensings)

    # 서버 요청
    response = requests.post(URL + '/rasp/drink/update', data = drink)
    # 응답 JSON 데이터 변환
    response = json.loads(response.text)

''' speak()
    @ option : 음성 옵션  "-v ko+f3 -s 160 -p 95"
    @ status : 현재 자판기의 상태
        (1) basic : 센싱되고 있지 않은 기본 상태
        (2) position : 손이 음료를 향해 위치한 상태
        (3) sold : 음료수가 팔린 상태
    @ idx : 음료의 포지션 인덱스 'position : ?'    
'''
# 스피커 출력 함수
def speak(option, status, idx=None) :
    message = ""
    # 자판기 상태 검사
    if status == "basic" :
        # 센싱되고 있지 않은 기본 상태

        # 자판기의 모든 음료 정보를 하나의 문자열로 병합
        names = ""
        for i, name in enumerate(drinks["name"]) : #[(0,'1234'),(1,'test2')...]
            names += str(i+1) + '번 : ' + name + ' : '
            
        message = "안녕하세요, 말하는 음료수 자판기입니다. 지금부터, 음료수 위치와, 이름, 가격을 말씀드리겠습니다. " + names
        
    elif status == "position" :
        # 손이 음료를 향해 위치한 상태  drinks["position"][idx] + '번: ' +
        message = '선택하신' + drinks["name"][idx] + '는 : ' + str(drinks["price"][idx]) + '원, 입니다.'
    elif status == "sold" :
        # 음료수가 팔린 상태
        message = drinks["name"][idx] + '를, 선택하셨습니다. : 맛있게 드시고 : 즐거운 하루 되십시오.'
    else :
        # 그 외
        pass

    # 스피커 출력
    os.system("espeak {} '{}'".format(option, message))

# 파일이 직접 실행됐다면 (모듈로써 사용된게 아니라면) 실행
if __name__ == "__main__":
    main()
