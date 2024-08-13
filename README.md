# pose-classification-service

Ассинхронный микросервис без хранения состояния классификации позы человека по ключевым точкам.</br>
1. В качестве классификатора используется подготовленная xgboost модель.</br>
2. Сервис работает в виде косьюмера Kafka событий. Каждое событие содержит набор фреймов с ключевыми точками.</br>
3. Результат классификации продьюсится далее по микросервисам [через](https://github.com/vadikko2/pose-detection-service/blob/801ede9273a38565e799362d978d1af0aeebec6c/src/consumer/service/points_handler.py#L16).
4. История кешируется в сециальном [хранилище](https://github.com/vadikko2/pose-detection-service/blob/801ede9273a38565e799362d978d1af0aeebec6c/src/consumer/service/points_handler.py#L26) для улучшения качества классификации. Текущая инфраструктура требует, чтобы результат продьюсился в Redis PUBSUB, а не дальше по Kafka. Абстракция позволяет заменить ResultProducer на любую имплементацию.</br>
