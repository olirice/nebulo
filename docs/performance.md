# Performance

**Performance Enabling Features:**

* All queries are handled in a single round-trip to the database so there are no [N+1 issues](https://stackoverflow.com/questions/97197/what-is-the-n1-selects-problem-in-orm-object-relational-mapping)
* SQL queries only fetch requested fields
* SQL queries return JSON which significantly reduces database IO when joins are present
* Fully async


**Benchmarks**

Performance depends on network, number of workers, log level etc. Despite all that, here are rough figures with Postgres and the web server running on a mid-tier 2017 Macbook Pro.

```text
Benchmarking 0.0.0.0 (be patient)


Server Software:        uvicorn
Server Hostname:        0.0.0.0
Server Port:            5034

Document Path:          /
Document Length:        310 bytes

Concurrency Level:      10
Time taken for tests:   5.571 seconds
Complete requests:      1000
Failed requests:        0
Total transferred:      436000 bytes
Total body sent:        245000
HTML transferred:       310000 bytes
Requests per second:    179.49 [#/sec] (mean)
Time per request:       55.712 [ms] (mean)
Time per request:       5.571 [ms] (mean, across all concurrent requests)
Transfer rate:          76.43 [Kbytes/sec] received
                        42.95 kb/s sent
                        119.37 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.0      0       0
Processing:    17   55  18.7     52      98
Waiting:       17   55  18.7     51      98
Total:         18   55  18.7     52      98

Percentage of the requests served within a certain time (ms)
  50%     52
  66%     60
  75%     65
  80%     69
  90%     80
  95%     90
  98%     94
  99%     95
 100%     98 (longest request)
```

So approximately 180 requests/second responding in sub 100 milliseconds.

Note that under normal load, response times are significantly faster.

```text
Percentage of the requests served within a certain time (ms)
  50%     17
  66%     19
  75%     19
  80%     20
  90%     21
  95%     24
  98%     26
  99%     30
 100%     38 (longest request)
```
