COMPOSE = docker compose

.PHONY: up down build logs ssl

up:
	$(COMPOSE) up -d

down:
	@read -p "Остановить landing? [yes/N]: " ans && [ "$${ans}" = "yes" ]
	$(COMPOSE) down

build:
	$(COMPOSE) up -d --build

logs:
	$(COMPOSE) logs -f nginx

ssl:
	@echo "Запускаем временный nginx для ACME-challenge..."
	docker run --rm -d --name etoir-landing-init \
		-p 80:80 \
		-v $(PWD)/nginx/etoir-init.conf:/etc/nginx/conf.d/default.conf:ro \
		-v etoir-landing_certbot-www:/var/www/certbot \
		nginx:1.27-alpine
	@echo "Получаем сертификат..."
	docker run --rm \
		-v etoir-landing_certbot-conf:/etc/letsencrypt \
		-v etoir-landing_certbot-www:/var/www/certbot \
		certbot/certbot certonly --webroot --expand \
		--webroot-path /var/www/certbot \
		-d etoir.ru -d www.etoir.ru -d e-toir.ru -d www.e-toir.ru \
		--email admin@e-toir.ru \
		--agree-tos --no-eff-email
	docker stop etoir-landing-init
	@echo "Запускаем nginx с SSL..."
	$(COMPOSE) up -d
