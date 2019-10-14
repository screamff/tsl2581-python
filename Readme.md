### 环境光传感器tsl2581
* 型号：微雪tsl2581
* 特点：i2c数据传输

### 与树莓派连线参考
![连线](connection.jpg)

### 运行
运行于`python3`环境，树莓派自带`smbus`，一般无需额外模块。<br>
测试时执行`python3 tsl2581.py`

作为模块导入:
```
from tsl2581 import TSl2581

# 初始化
sensor = TSl2581(1, 0x39)
sensor.power_on()
time.sleep(2)
sensor.config(gain_size=GAIN_1X)  # 参数需要与下面的caculateLux对应
# 读取数据
sensor.read_channel()
data = sensor.calculateLux(iGain=0)
# gain_size与iGain对应关系为：
# gain_size=GAIN_1X,iGain=0 | gain_size=GAIN_8X,iGain=1 | gain_size=GAIN_16X,iGain=2
