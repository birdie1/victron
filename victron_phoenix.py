from vedirect import Vedirect

class Phoenix:
    MODE = {
        2: "Inverter",
        4: "Off",
        5: "Eco",
        253: "Hibernate",
    }

    PID = {
        "0x203": "BMV-700",
        "0x204": "BMV-702",
        "0x205": "BMV-700H",
        "0xA042": "BlueSolar MPPT 75|15",
        "0xA043": "BlueSolar MPPT 100|15",
        "0xA046": "BlueSolar MPPT 150|70",
        "0xA047": "BlueSolar MPPT 150|100",
        "0xA049": "BlueSolar MPPT 100|50 rev2",
        "0xA04A": "BlueSolar MPPT 100|30 rev2",
        "0xA04B": "BlueSolar MPPT 150|35 rev2",
        "0xA04C": "BlueSolar MPPT 75|10",
        "0xA04D": "BlueSolar MPPT 150|45",
        "0xA04E": "BlueSolar MPPT 150|60",
        "0xA04F": "BlueSolar MPPT 150|85",
        "0xA050": "SmartSolar MPPT 250|100",
        "0xA053": "SmartSolar MPPT 75|15",
        "0xA054": "SmartSolar MPPT 75|10",
        "0xA055": "SmartSolar MPPT 100|15",
        "0xA056": "SmartSolar MPPT 100|30",
        "0xA057": "SmartSolar MPPT 100|50",
        "0xA058": "SmartSolar MPPT 150|35",
        "0xA059": "SmartSolar MPPT 150|100 rev2",
        "0xA05A": "SmartSolar MPPT 150|85 rev2",
        "0xA05B": "SmartSolar MPPT 250|70",
        "0xA05C": "SmartSolar MPPT 250|85",
        "0xA05D": "SmartSolar MPPT 250|60",
        "0xA05E": "SmartSolar MPPT 250|45",
        "0xA05F": "SmartSolar MPPT 100|20",
        "0xA060": "SmartSolar MPPT 100|20 48V",
        "0xA061": "SmartSolar MPPT 150|45",
        "0xA062": "SmartSolar MPPT 150|60",
        "0xA063": "SmartSolar MPPT 150|70",
        "0xA064": "SmartSolar MPPT 250|85 rev2",
        "0xA065": "SmartSolar MPPT 250|100 rev2",
        "0xA066": "BlueSolar MPPT 100|20",
        "0xA067": "BlueSolar MPPT 100|20 48V",
        "0xA068": "SmartSolar MPPT 250|60 rev2",
        "0xA069": "SmartSolar MPPT 250|70 rev2",
        "0xA06A": "SmartSolar MPPT 150|45 rev2",
        "0xA06B": "SmartSolar MPPT 150|60 rev2",
        "0xA06C": "SmartSolar MPPT 150|70 rev2",
        "0xA06D": "SmartSolar MPPT 150|85 rev3",
        "0xA06E": "SmartSolar MPPT 150|100 rev3",
        "0xA06F": "BlueSolar MPPT 150|45 rev2",
        "0xA070": "BlueSolar MPPT 150|60 rev2",
        "0xA071": "BlueSolar MPPT 150|70 rev2",
        "0xA102": "SmartSolar MPPT VE.Can 150/70",
        "0xA103": "SmartSolar MPPT VE.Can 150/45",
        "0xA104": "SmartSolar MPPT VE.Can 150/60",
        "0xA105": "SmartSolar MPPT VE.Can 150/85",
        "0xA106": "SmartSolar MPPT VE.Can 150/100",
        "0xA107": "SmartSolar MPPT VE.Can 250/45",
        "0xA108": "SmartSolar MPPT VE.Can 250/60",
        "0xA109": "SmartSolar MPPT VE.Can 250/70",
        "0xA10A": "SmartSolar MPPT VE.Can 250/85",
        "0xA10B": "SmartSolar MPPT VE.Can 250/100",
        "0xA10C": "SmartSolar MPPT VE.Can 150/70 rev2",
        "0xA10D": "SmartSolar MPPT VE.Can 150/85 rev2",
        "0xA10E": "SmartSolar MPPT VE.Can 150/100 rev2",
        "0xA10F": "BlueSolar MPPT VE.Can 150/100",
        "0xA112": "BlueSolar MPPT VE.Can 250/70",
        "0xA113": "BlueSolar MPPT VE.Can 250/100",
        "0xA114": "SmartSolar MPPT VE.Can 250/70 rev2",
        "0xA115": "SmartSolar MPPT VE.Can 250/100 rev2",
        "0xA116": "SmartSolar MPPT VE.Can 250/85 rev2",
        "0xA231": "Phoenix Inverter 12V 250VA 230V",
        "0xA232": "Phoenix Inverter 24V 250VA 230V",
        "0xA234": "Phoenix Inverter 48V 250VA 230V",
        "0xA239": "Phoenix Inverter 12V 250VA 120V",
        "0xA23A": "Phoenix Inverter 24V 250VA 120V",
        "0xA23C": "Phoenix Inverter 48V 250VA 120V",
        "0xA241": "Phoenix Inverter 12V 375VA 230V",
        "0xA242": "Phoenix Inverter 24V 375VA 230V",
        "0xA244": "Phoenix Inverter 48V 375VA 230V",
        "0xA249": "Phoenix Inverter 12V 375VA 120V",
        "0xA24A": "Phoenix Inverter 24V 375VA 120V",
        "0xA24C": "Phoenix Inverter 48V 375VA 120V",
        "0xA251": "Phoenix Inverter 12V 500VA 230V",
        "0xA252": "Phoenix Inverter 24V 500VA 230V",
        "0xA254": "Phoenix Inverter 48V 500VA 230V",
        "0xA259": "Phoenix Inverter 12V 500VA 120V",
        "0xA25A": "Phoenix Inverter 24V 500VA 120V",
        "0xA25C": "Phoenix Inverter 48V 500VA 120V",
        "0xA261": "Phoenix Inverter 12V 800VA 230V",
        "0xA262": "Phoenix Inverter 24V 800VA 230V",
        "0xA264": "Phoenix Inverter 48V 800VA 230V",
        "0xA269": "Phoenix Inverter 12V 800VA 120V",
        "0xA26A": "Phoenix Inverter 24V 800VA 120V",
        "0xA26C": "Phoenix Inverter 48V 800VA 120V",
        "0xA271": "Phoenix Inverter 12V 1200VA 230V",
        "0xA272": "Phoenix Inverter 24V 1200VA 230V",
        "0xA274": "Phoenix Inverter 48V 1200VA 230V",
        "0xA279": "Phoenix Inverter 12V 1200VA 120V",
        "0xA27A": "Phoenix Inverter 24V 1200VA 120V",
        "0xA27C": "Phoenix Inverter 48V 1200VA 120V",
        "0xA281": "Phoenix Inverter 12V 1600VA 230V",
        "0xA282": "Phoenix Inverter 24V 1600VA 230V",
        "0xA284": "Phoenix Inverter 48V 1600VA 230V",
        "0xA291": "Phoenix Inverter 12V 2000VA 230V",
        "0xA292": "Phoenix Inverter 24V 2000VA 230V",
        "0xA294": "Phoenix Inverter 48V 2000VA 230V",
        "0xA2A1": "Phoenix Inverter 12V 3000VA 230V",
        "0xA2A2": "Phoenix Inverter 24V 3000VA 230V",
        "0xA2A4": "Phoenix Inverter 48V 3000VA 230V",
        "0xA340": "Phoenix Smart IP43 Charger 12|50 (1+1)",
        "0xA341": "Phoenix Smart IP43 Charger 12|50 (3)",
        "0xA342": "Phoenix Smart IP43 Charger 24|25 (1+1)",
        "0xA343": "Phoenix Smart IP43 Charger 24|25 (3)",
        "0xA344": "Phoenix Smart IP43 Charger 12|30 (1+1)",
        "0xA345": "Phoenix Smart IP43 Charger 12|30 (3)",
        "0xA346": "Phoenix Smart IP43 Charger 24|16 (1+1)",
        "0xA347": "Phoenix Smart IP43 Charger 24|16 (3)" 
    }

    CS = {
        1: "Low power",
        2: "Fault",
        3: "Bulk",
        4: "Absorption",
        5: "Float",
        6: "Storage",
        7: "Equalize (manual)",
        9: "Inverting",
        11: "Power supply",
        245: "Starting-up",
        246: "Repeated absorption",
        247: "Auto equalize / Recondition",
        248: "BatterySafe",
        252: "External Control"
    }

    # WARN and AR has same codes, but different meanings
    # WARN is just a warning while AR (alarm reason) is the reason why the inverter went into security shutdown
    WARN_AR = {
        1: "Low Voltage",
        2: "High Voltage",
        4: "Low SOC",
        8: "Low Starter Voltage",
        16: "High Starter Voltage",
        32: "Low Temperature",
        64: "High Temperature",
        128: "Mid Voltage",
        256: "Overload",
        512: "DC-ripple",
        1024: "Low V AC out",
        2048: "High V AC out",
        4096: "Short Circuit",
        8192: "BMS Lockout"
    }

    DEVIDER = {
        'V': 1000,
        'AC_OUT_I': 10,
        'AC_OUT_V': 100
    }

    def __init__(self, name, port):
        self.name = name
        self.port = port

    def extract_firmware(self, fw_raw):
        if fw_raw[0] == 0:
            return f'{fw_raw[1:1]}.{fw_raw[2:]}'
        else:
            return f'{fw_raw[0:1]}{fw_raw[1:1]}.{fw_raw[2:]}'

    def extract_warn_ar(self, raw):
        raw_str = f"{raw}:"
        raw_helper = []
        for i in range(13, -1, -1):
            if (2 ** i) <= raw:
                raw_helper.append(self.WARN_AR[2 ** i])
                raw = raw - (2 ** i)
        return raw_str + "|".join(raw_helper)

    def format_data(self, data):
        new_dict = {}
        new_dict['firmware'] = self.extract_firmware(data['FW'])
        new_dict['serial'] = data['SER#']
        new_dict['production date'] = f"year: 20{data['SER#'][2:2]}, week: {data['SER#'][4:2]}"
        new_dict['product'] = f"{data['PID']}: {self.PID[data['PID']]}"
        new_dict['mode'] = f"{data['MODE']}: {self.MODE[int(data['MODE'])]}"
        new_dict['state'] = f"{data['CS']}: {self.CS[int(data['CS'])]}"
        new_dict['voltage'] = f"{(int(data['V']) / self.DEVIDER['V']):.2f}"
        new_dict['ac_voltage'] = f"{(int(data['AC_OUT_V']) / self.DEVIDER['AC_OUT_V']):.2f}"
        if int(data['AC_OUT_I']) <= 0:
            cur = 0
        else:
            cur = float(data['AC_OUT_I']) / self.DEVIDER['AC_OUT_I']
        new_dict['ac_current'] = f"{cur:.2f}"

        new_dict['alarm_reason'] = self.extract_warn_ar(int(data['AR']))
        new_dict['warning'] = self.extract_warn_ar(int(data['WARN']))

        return new_dict

    def get_data(self):
        ve = Vedirect(self.port, 60)
        return self.format_data(ve.read_data_single())
