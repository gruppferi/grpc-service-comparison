from modules.grpc_client_round_robin import app

if __name__ == '__main__':
    # Enable threading in the Flask development server
    app.run(host='0.0.0.0', port=5000, threaded=True)
