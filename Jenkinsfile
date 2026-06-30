pipeline {
    agent any

    environment {
        SONAR_HOST_URL    = 'http://localhost:9000'
        SONAR_PROJECT_KEY = 'restaurante_final'
        APP_PORT          = '8083'
        ZAP_HOST          = 'localhost'
        ZAP_PORT          = '8090'
        DOCKER_IMAGE      = "restaurante_final:${env.BUILD_NUMBER}"
    }

    // Trigger automático por commit: requiere el plugin "GitHub" instalado
    // y un webhook configurado en el repositorio remoto.
    // Para pruebas locales sin ese plugin, usa pollSCM en su lugar:
    // triggers {
    //     pollSCM('H/5 * * * *')   // revisa el repo cada 5 minutos
    // }
    triggers {
        githubPush()
    }

    stages {

        // ─────────────────────────────────────────
        // 1. CONSTRUCCIÓN AUTOMÁTICA
        // ─────────────────────────────────────────
        stage('1. Construccion Automatica') {
            steps {
                echo '>>> Instalando dependencias...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install gunicorn pytest-cov
                '''
            }
        }

        // ─────────────────────────────────────────
        // 2. ANÁLISIS ESTÁTICO — SonarQube
        // ─────────────────────────────────────────
        stage('2. Analisis Estatico - SonarQube') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=src \
                            -Dsonar.host.url=${SONAR_HOST_URL} \
                            -Dsonar.python.version=3.12 \
                            -Dsonar.python.coverage.reportPaths=coverage.xml
                    '''
                }
            }
        }

        stage('2b. Quality Gate') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        // ─────────────────────────────────────────
        // 3. PRUEBAS UNITARIAS — pytest + coverage
        // ─────────────────────────────────────────
        stage('3. Pruebas Unitarias') {
            steps {
                sh '''
                    . venv/bin/activate
                    export PYTHONPATH=src
                    pytest tests/domain/ tests/services/ tests/repositories/ \
                        --tb=short \
                        --junitxml=reports/unit-results.xml \
                        --cov=src \
                        --cov-report=xml:coverage.xml \
                        --cov-report=html:reports/coverage-html \
                        -v
                '''
            }
            post {
                always {
                    junit 'reports/unit-results.xml'
                    publishHTML(target: [
                        allowMissing: false,
                        reportDir:    'reports/coverage-html',
                        reportFiles:  'index.html',
                        reportName:   'Cobertura de Código'
                    ])
                }
            }
        }

        // ─────────────────────────────────────────
        // 4. PRUEBAS FUNCIONALES — Selenium
        // ─────────────────────────────────────────
        stage('4. Pruebas Funcionales - Selenium') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Levantar la app en background para Selenium
                    mkdir -p instance
                    export DATABASE_URL=sqlite:////${WORKSPACE}/instance/test_functional.db
                    export SECRET_KEY=test-secret
                    export ADMIN_INITIAL_PASSWORD=admin123
                    export STAFF_INITIAL_PASSWORD=staff123
                    python -c "
from src.main.python.web.app import initialize_database, app
initialize_database()
" 
                    gunicorn -w 1 -b 127.0.0.1:${APP_PORT} \
                        "src.main.python.web.app:app" \
                        --daemon \
                        --pid /tmp/gunicorn.pid \
                        --log-file /tmp/gunicorn.log

                    sleep 3

                    export PYTHONPATH=src
                    pytest tests/lab05/ \
                        --tb=short \
                        --junitxml=reports/functional-results.xml \
                        -v || true

                    # Detener la app
                    kill $(cat /tmp/gunicorn.pid) 2>/dev/null || true
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/functional-results.xml'
                }
            }
        }

        // ─────────────────────────────────────────
        // 5. PRUEBAS DE PERFORMANCE — JMeter
        // ─────────────────────────────────────────
        stage('5. Pruebas de Performance - JMeter') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Levantar app para JMeter
                    mkdir -p instance
                    export DATABASE_URL=sqlite:////${WORKSPACE}/instance/test_perf.db
                    export SECRET_KEY=test-secret
                    export ADMIN_INITIAL_PASSWORD=admin123
                    export STAFF_INITIAL_PASSWORD=staff123
                    python -c "
from src.main.python.web.app import initialize_database, app
initialize_database()
"
                    gunicorn -w 2 -b 127.0.0.1:${APP_PORT} \
                        "src.main.python.web.app:app" \
                        --daemon \
                        --pid /tmp/gunicorn_perf.pid \
                        --log-file /tmp/gunicorn_perf.log

                    sleep 3

                    # Ejecutar plan de prueba JMeter
                    jmeter -n \
                        -t tests/performance/restaurante_test_plan.jmx \
                        -l reports/jmeter-results.jtl \
                        -e -o reports/jmeter-html \
                        -Jhost=127.0.0.1 \
                        -Jport=${APP_PORT}

                    kill $(cat /tmp/gunicorn_perf.pid) 2>/dev/null || true
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: true,
                        reportDir:    'reports/jmeter-html',
                        reportFiles:  'index.html',
                        reportName:   'JMeter Performance Report'
                    ])
                    perfReport sourceDataFiles: 'reports/jmeter-results.jtl'
                }
            }
        }

        // ─────────────────────────────────────────
        // 6. PRUEBAS DE SEGURIDAD — OWASP ZAP
        // ─────────────────────────────────────────
        stage('6. Pruebas de Seguridad - OWASP ZAP') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Levantar app para ZAP
                    mkdir -p instance
                    export DATABASE_URL=sqlite:////${WORKSPACE}/instance/test_sec.db
                    export SECRET_KEY=test-secret
                    export ADMIN_INITIAL_PASSWORD=admin123
                    export STAFF_INITIAL_PASSWORD=staff123
                    python -c "
from src.main.python.web.app import initialize_database, app
initialize_database()
"
                    gunicorn -w 1 -b 127.0.0.1:${APP_PORT} \
                        "src.main.python.web.app:app" \
                        --daemon \
                        --pid /tmp/gunicorn_sec.pid \
                        --log-file /tmp/gunicorn_sec.log

                    sleep 3

                    mkdir -p reports/zap

                    # Escaneo pasivo con ZAP en modo daemon
                    zap.sh -daemon \
                        -port ${ZAP_PORT} \
                        -config api.disablekey=true \
                        -config scanner.attackOnStart=true &
                    ZAP_PID=$!
                    sleep 25

                    # Spider + escaneo activo
                    curl "http://${ZAP_HOST}:${ZAP_PORT}/JSON/spider/action/scan/?url=http://127.0.0.1:${APP_PORT}&maxChildren=10"
                    sleep 15

                    curl "http://${ZAP_HOST}:${ZAP_PORT}/JSON/ascan/action/scan/?url=http://127.0.0.1:${APP_PORT}&recurse=true"
                    sleep 30

                    # Exportar reporte HTML
                    curl "http://${ZAP_HOST}:${ZAP_PORT}/OTHER/core/other/htmlreport/" \
                        -o reports/zap/zap-report.html

                    # Detener ZAP y app
                    curl "http://${ZAP_HOST}:${ZAP_PORT}/JSON/core/action/shutdown/" || true
                    kill $ZAP_PID 2>/dev/null || true
                    kill $(cat /tmp/gunicorn_sec.pid) 2>/dev/null || true
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: true,
                        reportDir:    'reports/zap',
                        reportFiles:  'zap-report.html',
                        reportName:   'OWASP ZAP Security Report'
                    ])
                }
            }
        }

        // ─────────────────────────────────────────
        // 7. CONSTRUCCIÓN DOCKER IMAGE
        // ─────────────────────────────────────────
        stage('7. Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${DOCKER_IMAGE} .
                    docker tag ${DOCKER_IMAGE} restaurante_final:latest
                '''
            }
        }

        // ─────────────────────────────────────────
        // 8. DESPLIEGUE — Docker
        // ─────────────────────────────────────────
        stage('8. Despliegue Automatico') {
            steps {
                withCredentials([file(credentialsId: 'restaurante-env-file', variable: 'ENV_FILE')]) {
                    sh '''
                        # Detener contenedor anterior si existe
                        docker stop restaurante_app 2>/dev/null || true
                        docker rm   restaurante_app 2>/dev/null || true

                        # Levantar nuevo contenedor usando el .env inyectado
                        # de forma segura desde las credenciales de Jenkins
                        docker run -d \
                            --name restaurante_app \
                            --restart unless-stopped \
                            -p ${APP_PORT}:8083 \
                            --env-file ${ENV_FILE} \
                            restaurante_final:latest
                    '''
                }
            }
        }
    }

    // ─────────────────────────────────────────
    // NOTIFICACIONES POST-PIPELINE
    // ─────────────────────────────────────────
    post {
        success {
            echo "✅ Pipeline completado exitosamente — Build #${env.BUILD_NUMBER}"
            // Notificación a GitHub: requiere credenciales configuradas explícitamente.
            // Descomentar y ajustar cuando se tenga el token de GitHub en Jenkins:
            // githubNotify status: 'SUCCESS',
            //              description: 'Pipeline CI/CD OK',
            //              context: 'jenkins/pipeline',
            //              repo: 'restaurante_prueba',
            //              account: 'ChristianSaFl',
            //              credentialsId: 'github-token',
            //              sha: env.GIT_COMMIT
        }
        failure {
            echo "❌ Pipeline fallido — Build #${env.BUILD_NUMBER}"
            // githubNotify status: 'FAILURE',
            //              description: 'Pipeline CI/CD FAILED',
            //              context: 'jenkins/pipeline',
            //              repo: 'restaurante_prueba',
            //              account: 'ChristianSaFl',
            //              credentialsId: 'github-token',
            //              sha: env.GIT_COMMIT
        }
        always {
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            cleanWs()
        }
    }
}