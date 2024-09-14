import re
import json
import chardet

# Regex patterns
patter_provider  = re.compile(r'(?i)^==.*camera provider hal (?P<providerName>.*) static info.* (?P<noOfDevices>\d+) devices.*==$')
pattern_device = re.compile(r'(?i)^==.*Camera HAL device.*/(?P<device>\d+).*static information.*==$')
pattern_characteristics = re.compile(r'(?i).*camera (?P<camera>.*)characteristics:$')
pattern_keyvalue = re.compile(r'(?P<key>[a-zA-Z ]+): (?P<value>[\w]+)')
pattern_characteristics_key = re.compile(r'^\s*(?P<key>\w.+):\s*(?P<datatype>\w+)\[(?P<count>\d+)\]')
pattern_characteristics_value= re.compile(r'^\s*\[(?P<value>.*)\]$')
pattern_device_end = re.compile(r'(?i)^==.*Camera HAL device.*==$')
pattern_characteristics_size = re.compile(r'(?i).*camera metadata array:\s*(?P<size>(\d)+)\s*/.*entries')

# Detect the file's encoding
def detect_file_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read(10000)  # Read first 10,000 bytes for detection
        result = chardet.detect(raw_data)
    return result['encoding']

# Convert the file to UTF-8 if needed
def convert_to_utf8(input_file, output_file):
    current_encoding = detect_file_encoding(input_file)
    
    if current_encoding != 'utf-8':
        with open(input_file, 'r', encoding=current_encoding) as source_file:
            content = source_file.read()
        
        with open(output_file, 'w', encoding='utf-8') as target_file:
            target_file.write(content)
        
        print(f"File converted to UTF-8 from {current_encoding}")
    else:
        print("File is already in UTF-8.")


def parse_dumpsys(lines):
    result = None
    current_device = None
    current_physical_device = None
    current_characteristics = None
    last_characteristics_key = None

    read_camera_count = 0

    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        # Provider
        provider_match = patter_provider.match(line)
        if provider_match :
            result = provider_match.groupdict()
            result["devices"] = {}
            print("+ [provider]", result)
            continue

        # Device
        device_match = pattern_device.match(line)
        if device_match :
            device = device_match.groupdict()
            current_device = device
            deviceId = device["device"]
            result["devices"][deviceId] = device
            current_physical_device = None
            print("====================================================")
            print("+ [device]", device)
            print("----------------------------------------------------")
            continue

        # device end
        device_end_match = pattern_device_end.match(line)
        if device_end_match :
            current_device = None
            current_physical_device = None
            current_characteristics = None
            last_characteristics_key = None
            read_camera_count += 1
            if (read_camera_count >= int(result["noOfDevices"])) :
                print("Finished reading everything")
                return result
            continue

        # characteristics
        characteristics_match = pattern_characteristics.match(line)
        if characteristics_match : 
            characteristics = characteristics_match.groupdict('camera')
            print("new characteristics")
            characteristics["camera"] = characteristics["camera"].strip()
            if len(characteristics["camera"]) > 0:
                if "physicalCameras" not in current_device :
                    current_device["physicalCameras"] = []
                    current_device["physicalCameraCount"] = 0
                    current_device["isLogicalCamera"] = True
                print("+ [physical camera]", characteristics["camera"])
                physical_device = {
                    "physicalCameraId" : characteristics["camera"],
                    "characteristics" : {}
                }
                current_device["physicalCameras"].append(physical_device)
                current_device["physicalCameraCount"] = current_device["physicalCameraCount"] + 1
                current_physical_device = physical_device
            else :
                current_device["characteristics"] = {}
                current_physical_device = None


        # decide which characteristics object to fill
        current_characteristics = current_device
        if (current_physical_device != None) :
            current_characteristics = current_physical_device["characteristics"]
        if (current_characteristics and "characteristics" in current_characteristics) :
            current_characteristics = current_characteristics["characteristics"]


        # 
        characteristics_size_match = pattern_characteristics_size.match(line)
        if (characteristics_size_match) :
            if current_characteristics != None:
                current_characteristics["size"] = characteristics_size_match.groupdict()["size"]
            # print(characteristics_size_match.group())
            # print(characteristics_size_match.groupdict())
            continue

        # keyvalue 
        keyvalue_match = re.finditer(pattern_keyvalue, line)
        if keyvalue_match :
            for x in keyvalue_match : 
                k = x["key"].strip()
                v = x["value"].strip()
                # print(k, ":", v)
                if current_characteristics != None:
                    current_characteristics[k] = v
                elif result :
                    result[k] = v

        # characteristics key
        characteristics_key_match = pattern_characteristics_key.match(line)
        if characteristics_key_match :
            characteristics_key = characteristics_key_match.groupdict()
            characteristics_key["key"] = characteristics_key["key"].split("(")[0].strip()
            # print(characteristics_key)
            current_characteristics[characteristics_key["key"]] = {
                "datatype" : characteristics_key["datatype"],
                "count" :  characteristics_key["count"],
                "values" : []
            }
            last_characteristics_key = characteristics_key

        # characteristics value
        characteristics_value_match = pattern_characteristics_value.match(line)
        if characteristics_value_match :
            characteristics_value = characteristics_value_match.groupdict()
            # print(characteristics_value["value"])
            if last_characteristics_key != None :
                characteristics_value["value"] = parse_characteristic_value(characteristics_value["value"],\
                                                current_characteristics[last_characteristics_key["key"]]["datatype"])
                current_characteristics[last_characteristics_key["key"]]["values"] += characteristics_value["value"]

    return result

def parse_characteristic_value(val, datatype) :
    val = val.strip()
    result = None
    if (datatype == "rational") :
        result = val.replace(")", "),")[:-1].split(",")
        result = [value.strip() for value in result]
    elif (")" in val):
        result = val.replace(")", "),")[:-1].split(",")
        result = [value.strip() for value in result]
    else :
        result = val.split(" ")
    return result

def main(input_file = None, json_output_file = None):
    if input_file == None:
        input_file = 'input.txt'

    if json_output_file == None:
        json_output_file = 'output.json'
    

    utf8_file = "temp_utf.txt"
    print(detect_file_encoding(input_file))
    convert_to_utf8(input_file, utf8_file)
    print(detect_file_encoding(utf8_file))


    with open(utf8_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    parsed_data = parse_dumpsys(lines)

    # Writing the output to JSON file
    with open(json_output_file, 'w') as json_file:
        json.dump(parsed_data, json_file, indent=2)

if __name__ == "__main__":
    print("************************************")
    main()
    print("************************************")
    main("moto.txt", "moto_output.json")
    print("************************************")
