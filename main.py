import datetime, random, yaml, json

def application(env, start_response):

    #start_response('200 OK', [('Content-Type','application/json')])

    path = env['PATH_INFO'][1:]
    params = {}
    try:
        for p in env['QUERY_STRING'].split("&"):
            p = str(p).strip()
            if not p: continue
            key = p.split("=")[0]; value = p.split("=")[1]
            params[key] = value
    except:   
        res = {"Error":"Error parsing parameters"}
        return str( json.dumps(res) )

    #if path == "yidxsfpt/BRPortal/br/P100.jsp":  
    #    start_response('200 OK', [('Content-Type','text/html;charset=UTF-8')])
    #    res = open("P100.jsp").read()
    #    return str(res)
    
    res = {"Error":"The URL '"+ path +"' is not recognized."}
    print
    print res
    print
    
    return str( json.dumps(res) )



