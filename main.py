import re
import json

# Regex patterns
key_value_pattern = re.compile(r'^\s*(?P<key>[\w\s]+):\s*(?P<value>.*)$')
key_with_array_pattern = re.compile(r'^\s*(?P<key>\w.+):\s*(?P<datatype>\w+)\[(?P<count>\d+)\]')
value_pattern = re.compile(r'^\s*\[.*\]$')

patter_provider  = re.compile(r'(?i)^==.*camera provider hal (?P<providerName>.*) static info.* (?P<noOfDevices>\d+) devices.*==$')
pattern_device = re.compile(r'(?i)^==.*Camera HAL device.*/(?P<device>\d+).*static information.*==$')
pattern_characteristics = re.compile(r'(?i).*camera (?P<camera>.*)characteristics:$')
pattern_keyvalue = re.compile(r'(?P<key>[a-zA-Z ]+): (?P<value>[\w]+)')


# Physical camera 5 characteristics
# API2 camera characteristics:

def parse_dumpsys(lines):
    result = None
    current_device = None

    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        # Provider
        provider_match = patter_provider.match(line)
        if provider_match :
            result = provider_match.groupdict()
            result["devices"] = []
            print("+ [provider]", result)
            continue

        # Device
        device_match = pattern_device.match(line)
        if device_match :
            device = device_match.groupdict()
            current_device = device
            result["devices"].append(device)
            print("====================================================")
            print("+ [device]", device)
            print("----------------------------------------------------")
            continue

        characteristics_match = pattern_characteristics.match(line)
        if characteristics_match : 
            characteristics = characteristics_match.groupdict('camera')
            
            print("new characteristics")
            characteristics["camera"] = characteristics["camera"].strip()

            if len(characteristics["camera"]) > 0:
                if "physicalCameras" not in current_device :
                    current_device["physicalCameras"] = []
                    current_device["physicalCameraCount"] = 0
                print("+ [physical camera]", characteristics["camera"])
                current_device["physicalCameras"].append({
                    "physicalCameraId" : characteristics["camera"]
                })
                current_device["physicalCameraCount"] = current_device["physicalCameraCount"] + 1
            continue


        # keyvalue_match = re.finditer(pattern_keyvalue, line)
        # if keyvalue_match :
        #     for x in keyvalue_match : 
        #         print(x.groupdict())
        #         current_device[x["key"]] = x["value"]

                
            # keyvalue = {match.group('key').strip() : match.group('value').strip() for match in keyvalue_match if match.group('value').strip()}
            # if len(keyvalue) > 0 :
            #     print(keyvalue)



    # print(result)

    return result



def parse_dumpsys1(lines):
    result = {}
    stack = [{}]
    for line in lines:
        line = line.rstrip()

        if not line:
            continue

        # Check if the line defines a new device or section
        device_match = pattern_device.match(line)
        if device_match:
            new_device = {
                "service_id" : 00
            }
            print(device_match.groupdict())
            device_name = device_match.group('device').strip()
            print("new Deive ", device_name)
            # if isinstance(stack[-1], dict):
            #     stack[-1][device_name] = new_device
            # elif isinstance(stack[-1], list):
            #     stack[-1].append(new_device)
            # result.append(new_device)
            # print(result)
            continue

        # Check if the line is a key with a nested structure
        match = key_value_pattern.match(line)
        if match:
            key = match.group('key').strip()
            value = match.group('value').strip()

            # print(key, value)

            if value.endswith(':'):
                # Start a new nested object
                new_obj = {}
                if isinstance(stack[-1], dict):
                    stack[-1][key] = new_obj
                stack.append(new_obj)
            else:
                # Handle multiple key-value pairs on the same line
                pairs = value.split(',')
                for pair in pairs:
                    if ':' in pair:
                        k, v = map(str.strip, pair.split(':', 1))
                        if isinstance(stack[-1], dict):
                            stack[-1][k] = parse_value(v)
                    else:
                        # If no key-value delimiter, consider the entire pair as a key with an empty value
                        if isinstance(stack[-1], dict):
                            stack[-1][pair.strip()] = None
            continue

        # Check if the line matches the array pattern
        elif key_with_array_pattern.match(line):
            key_match = key_with_array_pattern.match(line)
            key = key_match.group('key').strip()
            datatype = key_match.group('datatype').strip()
            count = int(key_match.group('count').strip())
            if isinstance(stack[-1], dict):
                stack[-1][key] = {"datatype": datatype, "count": count}
            continue

        # Check if the line is a value (list of items)
        elif value_pattern.match(line):
            parsed_value = parse_value(line.strip())
            if isinstance(stack[-1], dict):
                stack[-1] = parsed_value
            elif isinstance(stack[-1], list):
                stack[-1].append(parsed_value)
            continue

        # Handle end of nested object
        elif line.startswith('=='):
            while len(stack) > 1 and not isinstance(stack[-1], list):
                stack.pop()

    return stack[0]

def parse_value(value):
    if value.startswith('[') and value.endswith(']'):
        # Safely evaluate the list, or handle it as a string if malformed
        try:
            return value[1:-1].split(" ")
        except (SyntaxError, NameError):
            return value
    return value

def main():
    input_file = 'test.txt'
    json_output_file = 'output.json'
    
    # Reading the input file and parsing it
    with open(input_file, 'r') as file:
        lines = file.readlines()

    parsed_data = parse_dumpsys(lines)

    # Writing the output to JSON file
    with open(json_output_file, 'w') as json_file:
        json.dump(parsed_data, json_file, indent=2)

if __name__ == "__main__":
    main()
