pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Run Functional Tests') {
            steps {
                sh 'python -m unittest discover -s tests/functionaltests'
            }
        }
        stage('Run Unit Tests') {
            steps {
                sh 'python -m unittest discover -s tests/unittests'
            }
        }
        stage('Run Integration Tests') {
            steps {
                sh 'python -m unittest discover -s tests/integrationtests'
            }
        }
    }
}
