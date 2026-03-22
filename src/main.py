from fastapi import FastAPI

app = FastAPI()

# Route decorator - connects URL path (i.e. endpoint) to a python function
# "/" is root URL
@app.get("/") 
def root():
    return {"message": "hello world"}

@app.get("/about")
def about():
    return {"message": "This is my first FastAPI application"}
