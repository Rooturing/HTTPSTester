# HTTPSTester

### Introduction

This program tests a website' deployment of HTTPS, including subdomains. We define that one website is possible to be described as one of the six categories:

- HTTPS_default: The website uses HTTPS by default (e.g. 302 redirect).
- HTTP_default: The website uses HTTP by default.
  - HTTPS_reachable: The website can be reached through HTTPS.
  - HTTP_only: The website only support HTTP.
- HTTPS_only: The website can't redirect from HTTP to HTTPS, but support HTTPS.
- HTTPS_error: Although the website support HTTPS (whether HTTPS_default/reachable), error(s) occurred (e.g. certificate verify failed).
- unreachable: The website return HTTP error code such as 404, 500.

This program contains three parts:

- get_fulldomains.py: Use crt.sh and Sublist3r to get all subdomains from the inputed domain name(s).
- get_https_test.py: Test what HTTPS deployment category the domain belongs to.
- get_report_from_ssllab.py: Query the SSL Labs' API and get a detailed report.

### Usage
`pip3 install -r requirements`

##### First step：

`python3 get_fulldomains.py example.com`

The result will be saved at folder 'domain/fulldomain'

###### Second step:

`python3 get_https_test.py example.com`

The result will be saved at folder 'report/test_https'

###### Third srep:

`python3 get_report_from_ssllab.py example.com`

The result will be saved at folder 'report/ssllab'


