# 📘 enums.py
from enum import Enum

class ClassType(str, Enum):
    LT = "LT"
    BT = "BT"
    TH = "TH"

class RegisterStatus(str, Enum):
    SUCCESS = "Đăng ký thành công"
    FULL = "Lớp đầy"
    WAITING = "Chờ duyệt"

class RegisterType(str, Enum):
    ONLINE = "Đăng ký online"
    OFFLINE = "Đăng ký trực tiếp"

class TrainingLevel(str, Enum):
    BACHELOR = "Cử nhân"
    ENGINEER = "Kỹ sư"
    MASTER = "Thạc sĩ"
    DOCTOR = "Tiến sĩ"

class LearningStatus(str, Enum):
    ACTIVE = "Học"
    DROPOUT = "Thôi học"
    FORCED = "Buộc thôi học"

class Gender(str, Enum):
    MALE = "Nam"
    FEMALE = "Nữ"

class YearLevel(str, Enum):
    Y1 = "Năm 1"
    Y2 = "Năm 2"
    Y3 = "Năm 3"
    Y4 = "Năm 4"
    Y5 = "Năm 5"

class WarningLevel(str, Enum):
    NONE = "Cảnh báo mức 0"
    LEVEL_1 = "Cảnh báo mức 1"
    LEVEL_2 = "Cảnh báo mức 2"
    LEVEL_3 = "Cảnh báo mức 3"
