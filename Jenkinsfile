pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup Virtual Environment') {
            steps {
                script {
                    // Create a virtual environment
                    sh 'python3 -m venv venv'
                    
                    // Activate the virtual environment and install dependencies
                    sh '''
                    source venv/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage('Run Functional Tests') {
            steps {
                script {
                    // Activate the virtual environment and run functional tests
                    sh '''
                    source venv/bin/activate
                    python3 -m unittest discover -s tests/functionaltests
                    '''
                }
            }
        }
        stage('Run Unit Tests') {
            steps {
                script {
                    // Activate the virtual environment and run unit tests
                    sh '''
                    source venv/bin/activate
                    python3 -m unittest discover -s tests/unittests
                    '''
                }
            }
        }
        stage('Run Integration Tests') {
            steps {
                script {
                    // Activate the virtual environment and run integration tests
                    sh '''
                    source venv/bin/activate
                    python3 -m unittest discover -s tests/integrationtests
                    '''
                }
            }
        }
    }
}
