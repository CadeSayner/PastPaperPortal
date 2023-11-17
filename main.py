import os
import zipfile
from flask import Flask, render_template, request, send_file
from io import BytesIO
from fuzzywuzzy import fuzz

app = Flask(__name__)

def fileNameToPath(s):
    out = "/".join(s.split("_"))
    print(out)
    return out

def create_zip(subjects, years, mid, sup):
    # Path to the subjects directory within your web app's root
    base_directory = os.path.join(os.path.dirname(__file__), 'subjects')
    
    # Create a BytesIO buffer to store the zip file
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Loop through selected subjects
        for subject in subjects:
            subject_folder = f'{subject}'
            # Create a folder for each subject
            zip_file.write(os.path.join(base_directory, subject_folder), subject_folder)

            # Loop through selected years for the subject
            for year in years:
                # Construct the path to the subject's year folder
                year_folder = os.path.join(subject_folder, str(year))

                # Create the subject's year folder in the zip file
                zip_file.write(os.path.join(base_directory, year_folder), year_folder)
                for d in os.listdir(os.path.join(base_directory, year_folder)):
                    if ((d == "Supplementary" ) and (not sup)):
                        continue
                    if ((d=="May-June") and (not mid)):
                        continue
                    session_folder = os.path.join(year_folder, d)
                    zip_file.write(os.path.join(base_directory, session_folder), session_folder)
                    for paper in os.listdir(os.path.join(base_directory, session_folder)):
                        paper_folder = os.path.join(session_folder, paper)
                        zip_file.write(os.path.join(base_directory, paper_folder), paper_folder)
                        for file in os.scandir(os.path.join(base_directory, paper_folder)):
                            dest = os.path.join(paper_folder, file.name)
                            zip_file.write(os.path.join(base_directory, dest), dest)
    zip_buffer.seek(0)
    return zip_buffer

@app.route('/past_papers')
def past_papers():
    return render_template('past_papers.html')

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/')
def index():
    # This is the route for the root path
    return 'Welcome to the root path!'

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/search/mathematics')
def search_mathematics():
    return render_template('search_results_mathematics.html')

@app.route('/search/physics')
def search_physics():
    return render_template('search_results_physics.html')

@app.route('/search/lifescience')
def search_lifescience():
    return render_template('search_results_lifescience.html')

@app.route('/search/english')
def search_english():
    return render_template('search_results_english.html')

@app.route('/search/tourism')
def search_tourism():
    return render_template('search_results_tourism.html')

@app.route('/search/accounting')
def search_accounting():
    return render_template('search_results_accounting.html')

@app.route('/search/afrikaans')
def search_afrikaans():
    return render_template('search_results_afrikaans.html')

@app.route('/search/isiZulu')
def search_isiZulu():
    return render_template('search_results_isiZulu.html')

@app.route('/process_request', methods=['POST'])
def process_request():
    # Retrieve form data
    years = request.form.getlist('timeframe')
    subjects = request.form.getlist('subjects')
    mid = request.form.get("midYear")
    sup = request.form.get('supplementary')
    if (mid == "on"):
        mid = True
    else:
        mid = False

    if(sup == "on"):
        sup = True
    else:
        sup = False
    zip_buffer = create_zip(subjects, years, mid, sup)
    return send_file(zip_buffer, download_name='past_papers.zip', as_attachment=True)

@app.route('/search_results')
def search_results():
    # Get the search query from the form submission
    paper_name = request.args.get('paper_name', '')
    f = open("filePaths.txt", "r")
    results = f.readlines()
    f.close()

    keyword_subjects_map = {"mathematics":["math", "maths"], "physical sciences":["physics"]}
    # Perform fuzzy matching and scoring
    processed_results = []
    for result in results:
        result = result.replace("\n", "")
        similarity_score_partial = fuzz.partial_ratio(paper_name.lower(), result.lower())
        similarity_score_token = fuzz.partial_token_sort_ratio(paper_name.lower(), result.lower())

        similarity_score = (similarity_score_partial + similarity_score_token)/2
        for subject in keyword_subjects_map.keys():
            if subject in result.lower() and paper_name.lower() in keyword_subjects_map.get(subject):
                # Boost searching
                similarity_score += 20
        if 'memo' in result.lower() and 'memo' in paper_name.lower():
            similarity_score += 10
        if 'Afrikaans' in result and 'Afrikaans' in paper_name:
            if result.index('Afrikaans') < 10:
                similarity_score += 10
                
        processed_results.append((result.replace('/', '_'), similarity_score))

    # Sort the results by similarity score
    processed_results.sort(key=lambda x: x[1], reverse=True)
    modified_results = [result[0].replace('/', '_') for result in processed_results][0:20]
    # Pass the results to the search_results.html template
    return render_template('search_results.html', results=modified_results)

@app.route('/download/<path>')
def download(path):
    print(path)
    # Process search here and display the search results
    # Serve the paper to the user here 
    return send_file(os.path.join(os.path.dirname(__file__), "subjects", fileNameToPath(path)), download_name=path, as_attachment=True)

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000, host='0.0.0.0')