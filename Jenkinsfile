pipeline {
    agent any

    environment {
        MONGO_USER = credentials('a00158d6-1aa3-4cb7-802d-bc6681b07688')
        MONGO_PASS = credentials('a00158d6-1aa3-4cb7-802d-bc6681b07688')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup Virtual Environment') {
            steps {
                script {
                    // Create a virtual environment in the new directory
                    sh '''
                    python3 -m venv /var/jenkins_home/venvs/CanItFarm
                    . /var/jenkins_home/venvs/CanItFarm/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage('Run Program with Tests') {
            steps {
                script {
                    // Activate the virtual environment and run the program with tests
                    sh '''
                    . /var/jenkins_home/venvs/CanItFarm/bin/activate
                    export MONGO_USER=${MONGO_USER}
                    export MONGO_PASS=${MONGO_PASS}
                    python3 your_program.py
                    python3 -m unittest discover -s tests/functionaltests
                    '''
                }
            }
        }
    }
}
