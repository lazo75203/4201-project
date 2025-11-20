
Intro to AI CSCE 4201 - Picture to Text Scanner Program
By Team 14 | Jihad Hamad and Martin Lazo:

We made this project for our UNT Intro to AI CSCE 4201 course, the goal was to upload/attach some picture file (png,jpeg,etc.) and have some sort of algorithm analyze it to extract the text and display it to the user
An OCR implemented from pytessaract is used for analyazation and text extraction, then we make a heuristiv based algorithm to loop analyzation until we get the best possible result for the user.

The following is how it can be ran/used:

Web Application:

We've deployed a web app of this project using Render web services, you can access it here: https://four201-project.onrender.com/
This opens the instance of our program from the main branch of the repository in GitHub, it may not be open at every oppurtunity, but message us directly in GitHub and we may be able to allow continued use when requested.


Terminal Running:

To run this program in your terminal, ensure that Python 3.8 or higher is installed on the running machine. Then install the required dependencies (libraries and python methods), you can use the commnad "pip install -r requirements.txt" to do this quickly, it's in the repo for ease of use/access.
You must also install Tesseract OCR the machine you are running this on if you choose to run it in terminal, you can find the installation instructions here: https://github.com/tesseract-ocr/tesseract.
After ensuring the requirements and Tessaract are installed, you can enter the command "python Extract.py" in the terminal of your local machine to run the program, it will make a flask server and give you a local host link to open in your browser to use the program.
