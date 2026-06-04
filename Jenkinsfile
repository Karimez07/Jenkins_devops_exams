pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    environment {
        DOCKERHUB_USER = 'sofianezy'

        MOVIE_IMAGE = "${DOCKERHUB_USER}/movie-service"
        CAST_IMAGE  = "${DOCKERHUB_USER}/cast-service"

        HELM_CHART = './charts'
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build images') {
            steps {
                sh """
                    docker build -t ${MOVIE_IMAGE}:${IMAGE_TAG} ./movie-service
                    docker build -t ${CAST_IMAGE}:${IMAGE_TAG} ./cast-service
                """
            }
        }

        stage('Push images to DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${MOVIE_IMAGE}:${IMAGE_TAG}
                        docker push ${CAST_IMAGE}:${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Helm lint') {
            steps {
                sh 'helm lint ./charts'
            }
        }

        stage('Deploy dev / qa / staging') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    ),
                    file(
                        credentialsId: 'kubeconfig',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    script {
                        def environments = [
                            [ns: 'dev',     moviePort: '30081', castPort: '30082'],
                            [ns: 'qa',      moviePort: '30083', castPort: '30084'],
                            [ns: 'staging', moviePort: '30085', castPort: '30086']
                        ]

                        environments.each { e ->
                            sh """
                                kubectl create namespace ${e.ns} --dry-run=client -o yaml | kubectl apply -f -

                                kubectl -n ${e.ns} create secret docker-registry regcred \
                                  --docker-server=https://index.docker.io/v1/ \
                                  --docker-username="$DOCKER_USER" \
                                  --docker-password='$DOCKER_PASS' \
                                  --docker-email=ci@example.com \
                                  --dry-run=client -o yaml | kubectl apply -f -

                                helm upgrade --install cast-service ${HELM_CHART} \
                                  -n ${e.ns} --create-namespace \
                                  --set fullnameOverride=cast-service \
                                  --set image.repository=${CAST_IMAGE} \
                                  --set image.tag=${IMAGE_TAG} \
                                  --set service.type=NodePort \
                                  --set service.nodePort=${e.castPort} \
                                  --wait --timeout 5m --atomic

                                helm upgrade --install movie-service ${HELM_CHART} \
                                  -n ${e.ns} --create-namespace \
                                  --set fullnameOverride=movie-service \
                                  --set image.repository=${MOVIE_IMAGE} \
                                  --set image.tag=${IMAGE_TAG} \
                                  --set service.type=NodePort \
                                  --set service.nodePort=${e.moviePort} \
                                  --set-string env[0].name=CAST_SERVICE_HOST_URL \
                                  --set-string env[0].value=http://cast-service:80/api/v1/casts/ \
                                  --wait --timeout 5m --atomic
                            """
                        }
                    }
                }
            }
        }

        stage('Deploy prod') {
            when {
                branch 'master'
            }
            steps {
                input message: 'Confirmer le déploiement en production ?', ok: 'Deploy'
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    ),
                    file(
                        credentialsId: 'kubeconfig',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh """
                        kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -

                        kubectl -n prod create secret docker-registry regcred \
                          --docker-server=https://index.docker.io/v1/ \
                          --docker-username="$DOCKER_USER" \
                          --docker-password='$DOCKER_PASS' \
                          --docker-email=ci@example.com \
                          --dry-run=client -o yaml | kubectl apply -f -

                        helm upgrade --install cast-service ${HELM_CHART} \
                          -n prod --create-namespace \
                          --set fullnameOverride=cast-service \
                          --set image.repository=${CAST_IMAGE} \
                          --set image.tag=${IMAGE_TAG} \
                          --set service.type=NodePort \
                          --set service.nodePort=30088 \
                          --wait --timeout 5m --atomic

                        helm upgrade --install movie-service ${HELM_CHART} \
                          -n prod --create-namespace \
                          --set fullnameOverride=movie-service \
                          --set image.repository=${MOVIE_IMAGE} \
                          --set image.tag=${IMAGE_TAG} \
                          --set service.type=NodePort \
                          --set service.nodePort=30087 \
                          --set-string env[0].name=CAST_SERVICE_HOST_URL \
                          --set-string env[0].value=http://cast-service:80/api/v1/casts/ \
                          --wait --timeout 5m --atomic
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline terminé avec succès.'
        }
        failure {
            echo 'Pipeline en échec. Vérifie les logs Jenkins.'
        }
    }
}
