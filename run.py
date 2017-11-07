from main import app, setup_db

setup_db();

app.run(debug=True,port=8085)
