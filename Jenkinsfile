pipeline {
  agent any
  environment {
    REGISTRY = 'docker.io/YOUR_USER'          // or Artifact Registry on GCP
    IMAGE    = "${REGISTRY}/orders-service:${env.GIT_COMMIT?.take(7) ?: 'local'}"
  }
  stages {
    stage('Test') {
      steps {
        sh '''
          python3 -m venv .venv && . .venv/bin/activate
          pip install -r app/requirements.txt
          cd app && pytest -q
        '''
      }
    }
    stage('Build image') {
      steps { sh 'docker build -t $IMAGE app/' }
    }
    stage('Push') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-creds',
                         usernameVariable: 'U', passwordVariable: 'P')]) {
          sh 'echo $P | docker login -u $U --password-stdin && docker push $IMAGE'
        }
      }
    }
    stage('Deploy to Kubernetes') {
      when { branch 'main' }
      steps {
        sh '''
          sed "s|IMAGE_PLACEHOLDER|$IMAGE|" k8s/deployment.yaml | kubectl apply -f -
          kubectl rollout status deployment/orders-service --timeout=120s
        '''
      }
    }
  }
  post {
    failure {
      // roll back if a deploy fails
      sh 'kubectl rollout undo deployment/orders-service || true'
    }
  }
}
