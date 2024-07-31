from rplidar import RPLidar, RPLidarException
#import smbus
import threading
import time
from waitress import serve
import json

#bus = smbus.SMBus(1)
#address = 8


#def send_data_to_arduino(data):
#    bus.write_byte(address, data)
#    print("raspberry pi sent: ", data)


lidar = RPLidar('/dev/ttyUSB0')

lidar.__init__('/dev/ttyUSB0', 115200, 3, None)

lidar.connect()

info = lidar.get_info()
print(info)

health = lidar.get_health()
print(health)

# LiDAR verilerini depolamak için global bir liste
scan_data = []
data_lock = threading.Lock()

try:

    for i, scan in enumerate(lidar.iter_scans()):
        temp_scan_data = []
        one_sent = False
        last_angle = None

        for d in scan:

            if 80 <= d[1] <= 100:

                if (d[2] / 10) <= 100:
                    one_sent = True
                    print(1)
                    #send_data_to_arduino(1)
                    break

                else:
                    one_sent = False
            angle = d[1]
            distance = d[2]

            # Açı değerlerini filtrele
            if 20 <= angle <= 160:
                temp_scan_data.append({'angle': angle, 'distance': distance})

            if last_angle is not None and angle < last_angle:
                with data_lock:
                    scan_data = temp_scan_data.copy()
                temp_scan_data = []
            last_angle = angle

            if last_angle is not None and abs((last_angle - d[1]) % 360) > 355:
                one_sent = False

            last_angle = d[1]

        if not one_sent:
            print(0)
            #send_data_to_arduino(0)
            one_sent = False

        if False:
            lidar.stop()
            lidar.stop_motor()
            lidar.disconnect()
            break

except KeyboardInterrupt as err:
    print('key board interupt')
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()

except RPLidarException as err:
    print(err)
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()

except AttributeError:
    print('hi attribute error')

# LiDAR verilerini toplayan bir iş parçacığı başlatın
thread = threading.Thread(target=collect_lidar_data)
thread.daemon = True
thread.start()


def simple_app(environ, start_response):
    with data_lock:
        response_body = json.dumps(scan_data).encode('utf-8')
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    return [response_body]

if __name__ == '__main__':
    serve(simple_app, host='0.0.0.0', port=9000)