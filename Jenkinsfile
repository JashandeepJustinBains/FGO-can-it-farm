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
                    // Create a virtual environment in the new directory
                    sh '''
                    python3 -m venv /var/jenkins_home/venvs/CanItFarm
                    . /var/jenkins_home/venvs/CanItFarm/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage('Run Functional Tests') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'a00158d6-1aa3-4cb7-802d-bc6681b07688', usernameVariable: 'MONGO_USER', passwordVariable: 'MONGO_PASS')]) {
                        // Activate the virtual environment and run functional tests
                        sh '''
                        . /var/jenkins_home/venvs/CanItFarm/bin/activate
                        export MONGO_USER=${MONGO_USER}
                        export MONGO_PASS=${MONGO_PASS}
                        python3 -m unittest discover -s tests/functionaltests
                        '''
                    }
                }
            }
        }
        stage('Run Unit Tests') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'a00158d6-1aa3-4cb7-802d-bc6681b07688', usernameVariable: 'MONGO_USER', passwordVariable: 'MONGO_PASS')]) {
                        // Activate the virtual environment and run unit tests
                        sh '''
                        . /var/jenkins_home/venvs/CanItFarm/bin/activate
                        python3 -m unittest discover -s tests/unittests
                        '''
                    }
                }
            }
        }
        stage('Run Integration Tests') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'a00158d6-1aa3-4cb7-802d-bc6681b07688', usernameVariable: 'MONGO_USER', passwordVariable: 'MONGO_PASS')]) {
                        // Activate the virtual environment and run integration tests
                        sh '''
                        . /var/jenkins_home/venvs/CanItFarm/bin/activate
                        python3 -m unittest discover -s tests/integrationtests
                        '''
                    }
                }
            }
        }
    }
}
