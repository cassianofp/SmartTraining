import mediapipe as mp
import cv2
import numpy as np
from flask import Flask
from flask import render_template
from flask import Response
import time

app = Flask(__name__)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    a = np.array(a)  # Primeiro Angulo
    b = np.array(b)  # Segundo Angulo - Ancora
    c = np.array(c)  # Terceiro Angulo

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
        np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)

    if angle > 180.0:
        angle = 360-angle

    return angle


def generate_biceps():
    # Setup do MediaPipe
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        counter = 0
        stage_1 = None
        stage_2 = None
        status = "COMECE"
        retorno = " "

        # Validação Frame por Frame
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            else:
                # Colorir para RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Fazer a detecção via MP
                results = pose.process(image)

                # Recolorir para BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # Extrair Marcações via MP
                try:
                    landmarks = results.pose_landmarks.landmark

                    # Pegar Cordenadas do corpo
                    shoulder_left = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                     landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow_left = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                                  landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist_left = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                                  landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    hip_left = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    shoulder_right = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                      landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    elbow_right = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                                   landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    wrist_right = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                                   landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    hip_right = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    # Calcular Angulo
                    angle1 = calculate_angle(
                        shoulder_left, elbow_left, wrist_left)
                    angle2 = calculate_angle(
                        elbow_left, shoulder_left, hip_left)
                    angle3 = calculate_angle(
                        shoulder_right, elbow_right, wrist_right)
                    angle4 = calculate_angle(
                        elbow_right, shoulder_right, hip_right)
                    # Visualizar Angulo - Testes
                    # cv2.putText(image, str(angle),
                    #            tuple(np.multiply(
                    #                elbow, [640, 480]).astype(int)),
                    #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,
                    #                                            255, 255), 2, cv2.LINE_AA)

                    # Logica do Contador - Validar amplitude
                    if angle1 > 160:
                        stage_1 = "down"
                    if angle1 < 30 and stage_1 == 'down':
                        stage_1 = "up"
                        counter += 1
                        print(counter)

                    if angle3 > 160:
                        stage_2 = "down"
                    if angle3 < 30 and stage_2 == 'down':
                        stage_2 = "up"
                        counter += 1
                        print(counter)

                    # Validar Distância do obro ao corpo
                    if angle2 <= 30 and angle4 <= 30:
                        status = "CORRETO"
                        retorno = " "
                    else:
                        status = "ERRADO"
                        retorno = "APROXIME O COTOVELO"
                except:
                    pass

                # Plotar informações na tela via OpenCV
                cv2.rectangle(image, (0, 0), (100, 100), (14, 65, 183), -1)

                # Render Rep
                cv2.putText(image, 'REPS', (20, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, str(counter),
                            (22, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Validação
                cv2.rectangle(image, (950, 0),
                              (1300, 100), (14, 65, 183), -1)
                cv2.putText(image, str(status),
                            (960, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Orientação
                cv2.putText(image, str(retorno),
                            (500, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (14, 65, 183), 2, cv2.LINE_AA)

                # Render Stage - Testes
                # cv2.putText(image, 'STAGE', (65, 12),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                # cv2.putText(image, stage,
                #             (60, 60),
                #             cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Detecções
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(
                                              color=(245, 66, 230), thickness=1, circle_radius=1),
                                          mp_drawing.DrawingSpec(
                                              color=(124, 252, 0), thickness=1, circle_radius=1)
                                          )

                # Transformar Frame em .jpg
                (flag, encodedImage) = cv2.imencode(".jpg", image)
                if not flag:
                    continue
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


def generate_agachamento():
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        up = False
        down = False
        count = 0
        stage: None
        status = "COMECE"
        retorno = " "
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            else:
                # Colorir para RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Fazer a detecção via MP
                results = pose.process(image)

                # Recolorir para BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    # Extrair Marcações via MP
                    landmarks = results.pose_landmarks.landmark

                    # Armazenar Cordenadas do corpo
                    cintura = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    joelho = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    calcanhar = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
                    cabeca = [landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].y]
                    ombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]

                    # Calcular angulo
                    angle1 = calculate_angle(cintura, joelho, calcanhar)
                    angle2 = calculate_angle(cabeca, ombro, cintura)

                    # Logica do contador - Validação de amplitude
                    if angle1 >= 160:
                        up = True
                        stage = "up"
                    if up == True and down == False and angle1 <= 60:
                        down = True
                        stage = "down"
                    if up == True and down == True and angle1 >= 160:
                        count += 1
                        up = False
                        down = False
                        stage = "up"
                        print(count)

                    # Validação do movimento - Coluna
                    if angle2 >= 160:
                        status = "CORRETO"
                        retorno = " "
                    else:
                        status = "ERRADO"
                        retorno = "ALINHE A COLUNA"

                except:
                    pass

                # Plotar informações na tela via OpenCV
                # Render Rep
                cv2.rectangle(image, (0, 0), (100, 100), (14, 65, 183), -1)
                cv2.putText(image, 'REPS', (20, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, str(count),
                            (22, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Validação
                cv2.rectangle(image, (950, 0),
                              (1300, 100), (14, 65, 183), -1)
                cv2.putText(image, str(status),
                            (960, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Orientação
                cv2.putText(image, str(retorno),
                            (500, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (14, 65, 183), 2, cv2.LINE_AA)

                # Render Stage - Testes
                # cv2.putText(image, 'STAGE', (65, 12),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                # cv2.putText(image, stage,
                #            (60, 60),
                #            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Angulo - Testes
                # cv2.putText(image, str(angle1),
                #            tuple(np.multiply(
                #                joelho, [640, 480]).astype(int)),
                #           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,
                #                                            255, 255), 2, cv2.LINE_AA
                #            )

                # Render Detecções
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(
                                              color=(245, 66, 230), thickness=1, circle_radius=1),
                                          mp_drawing.DrawingSpec(
                                              color=(124, 252, 0), thickness=1, circle_radius=1)
                                          )

                (flag, encodedImage) = cv2.imencode(".jpg", image)
                if not flag:
                    continue
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


def generate_thehundred():
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        up = False
        down = False
        count = 0
        stage: None
        status = "COMECE"
        retorno = " "
        segundos_inicio = 0
        segundos_final = 0
        segundos = 0

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            else:
                # Colorir para RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Fazer a detecção via MP
                results = pose.process(image)

                # Recolorir para BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    # Extrair Marcações via MP
                    landmarks = results.pose_landmarks.landmark

                    # Armazenar Cordenadas do corpo
                    cotovelo = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    pulso = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    cintura = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    joelho = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    calcanhar = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
                    cabeca = [landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].y]
                    ombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    calcanhar = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
                    # Calcular angulo
                    angle1 = calculate_angle(ombro, cintura, calcanhar)
                    angle2 = calculate_angle(pulso, cotovelo, ombro)
                    angle3 = calculate_angle(cabeca, ombro, cintura)

                    # Contador de segundos

                    # Validação da Pose e contador de segundos
                    if angle1 <= 135 and angle2 >= 160 and angle3 <= 130:
                        status = "CORRETO"
                        retorno = " "
                        if segundos_inicio == 0:
                            segundos_inicio = time.time()
                        count = int(time.time() - segundos_inicio)
                    else:
                        segundos_inicio = 0
                        if angle1 >= 135:
                            status = "ERRADO"
                            retorno = "LEVANTE AS PERNAS"
                        if angle2 <= 160:
                            status = "ERRADO"
                            retorno = "ENDIREITE OS BRACOS"
                        if angle3 >= 130:
                            status = "ERRADO"
                            retorno = "LEVANTE A CABECA"

                except:
                    pass

                # Plotar informações na tela via OpenCV
                # Render Rep
                cv2.rectangle(image, (0, 0), (200, 100), (14, 65, 183), -1)
                cv2.putText(image, 'REPS', (20, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, str(count),
                            (22, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Validação
                cv2.rectangle(image, (950, 0),
                              (1300, 100), (14, 65, 183), -1)
                cv2.putText(image, str(status),
                            (960, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Orientação
                cv2.putText(image, str(retorno),
                            (500, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (14, 65, 183), 2, cv2.LINE_AA)

                # Render Stage - Testes
                # cv2.putText(image, 'STAGE', (65, 12),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                # cv2.putText(image, stage,
                #            (60, 60),
                #            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

                # Render Angulo - Testes
                # cv2.putText(image, str(angle1),
                #            tuple(np.multiply(
                #                joelho, [640, 480]).astype(int)),
                #           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,
                #                                            255, 255), 2, cv2.LINE_AA
                #            )

                # Render Detecções
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(
                                              color=(245, 66, 230), thickness=1, circle_radius=1),
                                          mp_drawing.DrawingSpec(
                                              color=(124, 252, 0), thickness=1, circle_radius=1)
                                          )

                (flag, encodedImage) = cv2.imencode(".jpg", image)
                if not flag:
                    continue
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/agachamento')
def agachamento():
    return render_template('agachamento.html')


@app.route('/roscaalternada')
def roscaalternada():
    return render_template('roscaalternada.html')


@app.route('/thehundred')
def thehundred():
    return render_template('thehundred.html')


@app.route('/video_biceps')
def video_biceps():
    return Response(generate_biceps(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_agachamento')
def video_agachamento():
    return Response(generate_agachamento(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_thehundred')
def video_thehundred():
    return Response(generate_thehundred(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)

cap.release()
