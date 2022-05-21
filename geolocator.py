from requests import session
from time import time
from datetime import datetime
from os import path, mkdir
from re import compile
from json import loads as json_load


def config_key_invalid(key, value, instance):
    return key not in value or not isinstance(value[key], instance)
def build_full_dir(fpath):
    if fpath.count('/') == 0:
        if fpath.count('\\') == 0:
            return
        char = '\\'
    else:
        char = '/'
    start = fpath.rfind(char)
    dirpaths = []
    while start != -1:
        dirpaths.append(fpath[0:start])
        if path.exists(dirpaths[-1]):
            dirpaths.pop()
            break
        start = dirpaths[-1].rfind(char)
    for dirpath in dirpaths[::-1]:
        mkdir(dirpath)
class geolocator():
    MAX_BULK_IP_REQUESTS = 50
    BASE_URL = "https://api.ipgeolocation.io/"
    def get_bulk_ips_file(self,fpath):
        with open(fpath,'r') as f:
            return list(map(lambda x: x.strip(), f.read().split('\n')))
    def config_geolocator(self,CONFIG_FILE_PATH=None,CONFIG_DICT=None):
        def config_from_file(CONFIG_FILE_PATH):
            while True:
                try:
                    with open(CONFIG_FILE_PATH, 'r') as f:
                        return json_load(f.read())
                except Exception as e:
                    print(f"ERROR LOADING {repr(CONFIG_FILE_PATH)}: {repr(e)} please reformat the file and try again.")
                    input('>')
        if CONFIG_FILE_PATH is not None:
            config_dict = config_from_file(CONFIG_FILE_PATH)
        elif CONFIG_DICT is not None:
            config_dict = CONFIG_DICT
        else:
            raise Exception("neither CONFIG_FILE_PATH nor CONFIG_DICT were supplied to geolocator class!")
        for key, value in config_dict.items():
            match key:
                case "APIKEY":
                    self.APIKEY = value
                case "MAX_REQUESTS":
                    self.MAX_REQUESTS = value
                case "FIND_BULK_IPS":
                    if "REPEAT" not in value or value["REPEAT"] is None:
                        repeat = 1
                    else:
                        assert isinstance(value["REPEAT"],int)
                        repeat = value["REPEAT"]
                    if ("FILEPATH" not in value or not isinstance(value["FILEPATH"], str)):
                        if ("IPS" not in value or not isinstance(value["IPS"],list)):# list of IPS in json
                            raise Exception("'FIND_BULK_IPS' was specified in config file but no ip addresses were given!")
                        else:
                            ips = value["IPS"]
                    else:
                        ips = self.get_bulk_ips_file(value["FILEPATH"])# filepath to list of IPS
                    if ("OUTPUTFILE" not in value or not isinstance(value["OUTPUTFILE"], str)):
                        raise Exception("No output file as specified for storing requests of 'FIND_BULK_IPS'!")
                    else:
                        oputf = value["OUTPUTFILE"]
                    for rep in range(repeat):
                        for ip_breakdown in range(0,len(ips),geolocator.MAX_BULK_IP_REQUESTS):
                            self.REQUESTS.append(
                                request_obj(parent = self,
                                            endpoint="ipgeo-bulk",
                                            method="POST",
                                            outputfile=oputf,
                                            parameters={"ips":ips[ip_breakdown:min(len(ips)-1,ip_breakdown+geolocator.MAX_BULK_IP_REQUESTS)]}
                                            )
                            )
                case "LOOKUP_IP":
                    if config_key_invalid("IP",value,str):
                        raise Exception("IP was not included in 'LOOKUP_IP'!")
                    else:
                        ip = value["IP"]
                    if config_key_invalid("REPEAT",value,int):
                        repeat=1
                    else:
                        repeat=value["REPEAT"]
                    if config_key_invalid("OUTPUTFILE",value,str):
                        raise Exception("'OUTPUTFILE' missing from 'LOOKUP_IP'!")
                    else:
                        oputf=value["OUTPUTFILE"]
                    for rep in range(repeat):
                        self.REQUESTS.append(
                            request_obj(parent = self,
                                        endpoint="ipgeo",
                                        method="GET",
                                        outputfile=oputf,
                                        parameters={"ip":ip}
                                        )
                        )
    def log(self,line):
        if self.LOGFILE is not None:
            with open(self.LOGFILE,'a') as f:
                f.write(datetime.fromtimestamp(int(time())).isoformat() + '\t' + line + '\n')
    def write_result(self,content,fpath):
        ## ASSUMED THAT WRITE DIR WAS MADE IN BUILD_FULL_DIR
        with open(fpath,'wb') as f:
            f.write(content + b'\r\n')
    def run_through_requests(self):
        requests_counter = 0
        for req in self.REQUESTS:
            req.parameters["apiKey"] = self.APIKEY
        with session() as s:
            breakall = False
            for _ in range(self.MAX_REQUESTS):
                for req in self.REQUESTS:
                    requests_counter += 1
                    if requests_counter > self.MAX_REQUESTS:
                        breakall = True
                        break
                    resp = s.request(method=req.method,url=geolocator.BASE_URL + req.endpoint,params=req.parameters)
                    self.log(f"{req.method,req.endpoint,resp.status_code,resp.reason}")
                    self.write_result(resp.content,req.outputfile)
                if breakall:
                    break
    def __init__(self,CONFIG_FILE_PATH=None,CONFIG_DICT=None,logfile=None):
        print(CONFIG_FILE_PATH)
        self.LOGFILE = logfile
        if logfile is not None:
            build_full_dir(logfile)
        self.APIKEY = None
        self.MAX_REQUESTS = 0
        self.REQUESTS = []
        self.OUTPUT_FILE_PATH = None
        self.config_geolocator(CONFIG_FILE_PATH=CONFIG_FILE_PATH)

class request_obj():
    def __init__(self, parent, endpoint, method, parameters, outputfile):
        self.endpoint = endpoint
        self.method = method
        self.outputfile = outputfile
        build_full_dir(outputfile)
        self.parameters = parameters
    def make_request(self,sessionobj):
        pass


if __name__ == "__main__":
    my_geolocat = geolocator("CONFIG_free.json",logfile="REQUEST_LOG.txt")
    my_geolocat.run_through_requests()