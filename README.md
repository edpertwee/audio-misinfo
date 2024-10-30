# A scalable approach to identifying misinformation in audio media.
This repository contains the code for a project to develop a scalable method to identify misinformation in audio media. It forms the basis of a forthcoming paper that will test the approach using a case study of polio vaccine misinformation in US podcasts.

At a high level, the approach comprises four key steps: (1) identification of potentially relevant audio content using social listening software; (2) machine transcription of audio content identified during (1); (3) topic modelling of transcripts to identify latent topics; and (4) manual inspection of model outputs by human analysts with domain expertise.

## Scripts
The repository currently contains the following scripts:
- `data_prep.py`: Takes raw data on relevant podcast episodes outputted by a social listening tool, removes duplicates, and formats variable names to be human-readable.
- `file_downloader.py`: Extracts a list of podcast episode URLs from the social listening data and downloads the original audio files.
- `audio_transcriber.py`: Transcribes audio files using [OpenAI's Whisper model](https://openai.com/index/whisper/). Looks for a plain text file named `openai_api_key.txt` in the root directory, containing the API key.
- `transcript_preprocess.py`: Breaks the transcripts into segments using [Cohere's Command R+ model](https://docs.cohere.com/docs/command-r-plus) and extracts segments containing relevant keywords. Looks for a plain text file named `cohere_api_key.txt` in the root directory, containing the API key.
- `topic_model.ipynb`: Notebook containing code for the topic model, which uses [BERTopic](https://maartengr.github.io/BERTopic/index.html).

## Utilities
The repository also contains two utility files:
- `cost_calculator.ipynb`: Code to calculate the duration and transcription cost of a set of audio files. Inputs: source directory for audio files; transcription cost in $ per minute.
- `random_selector.ipynb`: Code to extract a random sample of transcripts for manual validation and checking.

## Acknowledgments
This work was supported by the AIR@InnoHK administered by the Innovation and Technology Commission, as well as the MSD Investigator Studies Program.

## Contact us
If you have any questions or want to access the data, please email:
ed.pertwee@lshtm.ac.uk
