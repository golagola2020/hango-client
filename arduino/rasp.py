# 모듈포함
import os
import serial
import json
import requests
import pprint

# 초기 세팅
PORT = '/dev/ttyACM0'
SERIAL_NUMBER = '20200814042555141'

# 데이터 요청 Domain 선언
URL = 'http://localhost:80'

# 전역 변수 선언
sensings = {} # 센싱된 데이터가 키와 값으로 저장될 딕셔너리 
received_keys = set() # 아두이노에게 전달 받을 변수명 집합
basic_keys = {'sensed_position', 'sold_position', 'state'} # 라즈베리파이가 가공할 변수명 집합

# 서버에서 전달받은 음료 정보가 저장될 전역 변수
drinks = {
    'position' : [],
    'name' : [],
    'price' : [],
}
    
# 메인 함수
def main():

    # 아두이노와 시리얼 통신할 인스턴스 생성 
    port = serial.Serial(
        port = PORT,
        baudrate = 9600
    )
    port.flushInput()

    # 음료수 정보 요청
    requestDrinks()

    # 무한 반복
    while True:
        
        # 아두이노에서 센싱된 데이터가 있으면 실행 
        if port.readable() :
            # 센싱 데이터 한 줄 단위로 수신
            receive = port.readline()
            # 이용 가능한 데이터인지 검사
            receive = is_available(receive)

            # 이용 가능한 데이터라면 실행 
            if receive :
                # 수신한 변수명 저장 
                received_keys.add(receive[0])
                
                print('receive :', receive)

                # 변수명과 값의 형태로 저장
                sensings[ receive[0] ] = receive[1]

                # 라즈베리파이가 가공할 데이터를 모두 수신 했다면 실행 
                if basic_keys.difference(received_keys) == set():
                    # 판매된 음료수가 있을 경우에 실행
                    if sensings["sold_position"] != "non" :
                        # 판매된 음료수 정보 차감 요청
                        requestDrinksUpdate()
                    

                    # 수신한 변수명 집합 비우기 => 다음 센싱 때에도 정상 수신하는지 검사하기 위함 
                    received_keys.clear()
            else :
                print("수신 가능한 센싱 데이터가 아닙니다.")

        # 아두이노에서 센싱된 데이터가 없으면 실행 
        else :
            print("센싱 데이터가 없습니다.")

            # 음료수 정보 요청
            requestDrinks()
            
                
# 아두이노에게 수신한 데이터가 사용가능한 데이터인지 검사하는 함수 
def is_available(receive) :
    # 바이트형을 기본 문자열형으로 디코딩
    receive = list(map(lambda rcv : rcv.decode(), receive.split()))

    # 수신한 변수명이 라즈베리파이에서 가공하고자하는 변수명들 중에 존재하는지 검사
    if receive[0] in basic_keys :
        # 존재한다면 수신 데이터 반환 
        return receive
    
    # 존재하지 않는다면 False 반환
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

# 판매된 음료수 정보 차감 요청 함수
def requestDrinksUpdate() :
    # 서버에게 요청할 데이터 생성
    drink = {
        'serial_number' : SERIAL_NUMBER, #if you pull server, then serialNumber -> serial_number
        'sold_position' : 1 # sensings["sensed_position"] #drink -> sold_position
    }
                            
    print('sensings : ', sensings)

    # 서버 요청
    response = requests.post(URL + '/rasp/drink/update', data = drink)
    # 응답 JSON 데이터 변환
    response = json.loads(response.text)

''' speak()
    @ option : 음성 옵션
    @ message : 스피커 출력 메세지
    @ status : 현재 자판기의 상태
        (1) basic : 센싱되고 있지 않은 기본 상태
        (2) position : 손이 음료를 향해 위치한 상태
        (3) sold : 음료수가 팔린 상태
    @ idx : 음료의 포지션 인덱스
'''
# 스피커 출력 함수
def speak(option, message, status, idx) :
    # 자판기 상태 검사
    if status == "basic" :
        # 센싱되고 있지 않은 기본 상태

        # 자판기의 모든 음료 정보를 하나의 문자열로 병합
        names = ""
        for i, name in enumerate(drinks["name"]) :
            names += str(i+1) + '번 : ' + name + ' : '
            
        message = "안녕하세요, 말하는 음료수 자판기입니다. 지금부터, 음료수 위치와, 이름, 가격을 말씀드리겠습니다. " + names
        
    elif status == "position" :
        # 손이 음료를 향해 위치한 상태
        message = drinks["name"][idx] + '는 : ' + drinks["price"][idx] + '원, 입니다.'
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