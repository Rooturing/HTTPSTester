# HTTPSTester

### Introduction

      _   _ _____ _____ ____  ____ _____         _            
     | | | |_   _|_   _|  _ \/ ___|_   _|__  ___| |_ ___ _ __ 
     | |_| | | |   | | | |_) \___ \ | |/ _ \/ __| __/ _ \ '__|
     |  _  | | |   | | |  __/ ___) || |  __/\__ \ ||  __/ |   
     |_| |_| |_|   |_| |_|   |____/ |_|\___||___/\__\___|_|  
    
      A Large-scale HTTPS evaluation tool with high performance.

This program tests a website' deployment of HTTPS, including subdomains. We define that one website is possible to be described as one of the six categories:

- HTTPS_default: The website uses HTTPS by default (e.g. 302 redirect).
- HTTP_default: The website uses HTTP by default.
  - HTTPS_reachable: The website can be reached through HTTPS.
  - HTTP_only: The website only support HTTP.
- HTTPS_only: The website can't redirect from HTTP to HTTPS, but support HTTPS.
- HTTPS_error: Although the website support HTTPS (whether HTTPS_default/reachable), error(s) occurred (e.g. certificate verify failed).
- unreachable: The website return HTTP error code such as 404, 500.

This program contains four parts:

- get_fulldomains.py: Use crt.sh and Sublist3r to get all subdomains from the inputed domain name(s).
- get_https_test.py: Test what HTTPS deployment category the domain belongs to.
- get_report_from_ssllab.py: Query the SSL Labs' API and get a detailed report.
- generate_full_report.py: Sum up the report, draw piechart, and output json file.

```
HTTPSTester# tree -d
.
├── output
│   ├── domain
│   │   ├── crtsh
│   │   ├── dnsres
│   │   ├── fulldomain
│   │   └── resolved_domain
│   └── report
│       ├── cert
│       │   ├── cert_ct
│       │   ├── cert_from_domain
│       │   ├── cert_from_ip
│       │   └── shared_cert
│       ├── chart
│       ├── domain_ip
│       ├── error_domain
│       ├── pic
│       ├── ssllab
│       │   └── raw_results
│       └── test_https
│           └── log
└── scripts
    └── util
        ├── log
        └── Sublist3r
            └── subbrute

```
### Usage
#### Preparation

+ pip3 install -r requirements
+ install mysql and create user/database
+ change config.py to configure your database

#### Integrated run

OPTIONS:
```
  -h, --help            show this help message and exit
  -s [SUBDOMAIN], --subdomain [SUBDOMAIN]
                        Test all the subdomains as well
  -d DOMAIN, --domain DOMAIN
                        Domian to be tested
  -f FILENAME, --filename FILENAME
                        Filename that contains a list of domains to be tested
  -m {test_all,get_fulldomain,get_https_test,get_report_from_ssllab,generate_full_report,test_none}, --module {test_all,get_fulldomain,get_https_test,get_report_from_ssllab,generate_full_report,test_none}
                        What test module would you like to perform?
  -o {file,database}, --output {file,database}
                        Choose the form of output of test results (file by
                        default)
```
EXAMPLES:

`python3 httpstester.py -d example.com -m get_fulldomain -o database`

#### Separated run
###### First step：

`python3 get_fulldomains.py example.com`

The result will be saved at folder 'output/domain/fulldomain'.

###### Second step:

`python3 get_https_test.py example.com`

The result will be saved at folder 'output/report/test_https'.

###### Third step:

`python3 get_report_from_ssllab.py example.com`

The result will be saved at folder 'output/report/ssllab'.

###### Fourth step:

`python3 generate_full_report.py example.com`

The program will sum up of the tested results and output piechar as well as json file in the 'output/report/pic (and chart)' directory.

###### Further work

Figure out ways to test if there exists login window in the domain we test.
