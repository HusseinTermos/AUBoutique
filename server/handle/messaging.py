from formatting import prep_json, build_http_response

def handle_get_messaging_info(request, active_users, requested_id):
    if requested_id not in active_users:
        return build_http_response(status_code=404,
                                body=prep_json({"message": "No messaging info found",}))

    messaging_ip, messaging_port, _ = active_users[requested_id]
    
    return build_http_response(status_code=200,
                               body=prep_json({"message": "messaging info sent successfully",
                                               "messaging_info":
                                               {"ip_addr": messaging_ip, "port": messaging_port}}))

     

def handle_post_messaging_info(request, active_users, addr):
    messaging_ip = request["body"]["ip_addr"]
    messaging_port = request["body"]["port"]
    user_id = request["body"]["user_id"]
    active_users[user_id] = (messaging_ip, messaging_port, addr)
    print(active_users)
    return build_http_response(status_code=200,
                               body=prep_json({"message": "messaging info received successfully"}))
    