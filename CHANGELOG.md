# Changelog

## [3.0.0](https://github.com/cyr-ius/wireguard-ui/compare/2.6.2...3.0.0) (2026-11-09)


### ⚠ BREAKING CHANGES

* GLOBAL_RATE_LIMIT_MAX / GLOBAL_RATE_LIMIT_WINDOW are renamed and no longer read; use the RATE_LIMIT_* variables instead.

### Features

* add auth_source column to users table ([395b043](https://github.com/cyr-ius/wireguard-ui/commit/395b043030769fdfa46cac77800f97785c80a7b8))
* add FastAPI and SQLModel skills, remove outdated templates ([6531444](https://github.com/cyr-ius/wireguard-ui/commit/6531444b92bfed807629ed6e127279fd0b6476bd))
* add global per-IP rate limiting middleware ([3269930](https://github.com/cyr-ius/wireguard-ui/commit/32699307fc8e26a1c358d9504d62ffd59d5b084f))
* add stricter auth tier and toggle to rate limiting ([a4ab671](https://github.com/cyr-ius/wireguard-ui/commit/a4ab671d1029a7ce23255f08095b0bf53a8b3f58))
* add SWAGGER_ENABLED env var to disable API docs ([f1e2276](https://github.com/cyr-ius/wireguard-ui/commit/f1e2276999ccd087cde1a4a3f9ce76463a6fe498))
* add user profile page and password change support ([fb9e9c5](https://github.com/cyr-ius/wireguard-ui/commit/fb9e9c5d72422ce90f6c0ecdf23d571b0da27529))
* ajouter des fonctionnalités Python, Prek et UV au fichier devcontainer ([3680bc7](https://github.com/cyr-ius/wireguard-ui/commit/3680bc7a81679c9dd21bcbf6917fabf1a066f747))
* ajouter la gestion des cookies d'authentification et protection CSRF ([db304ed](https://github.com/cyr-ius/wireguard-ui/commit/db304ed30f26904b421cd7c9c6da7d754f678566))
* ajouter un limiteur de taux pour les tentatives de connexion et valider les adresses IP ([cf8f17f](https://github.com/cyr-ius/wireguard-ui/commit/cf8f17f89c62be68b9ba4d20cdc181af3b4ad096))
* ajouter un script d'installation des dépendances système pour WireGuard UI ([4ef2249](https://github.com/cyr-ius/wireguard-ui/commit/4ef2249a93fee1cf35472eb8effcb4df14c14db0))
* ajouter un script de publication pour gérer les versions et les tags ([2541cb8](https://github.com/cyr-ius/wireguard-ui/commit/2541cb8a92f7e7f9df62242a5201b62ab6b5074b))
* ajouter une commande onCreate pour installer les dépendances système ([478de45](https://github.com/cyr-ius/wireguard-ui/commit/478de459c692ec6a3427afd4768be216104f04a3))
* améliorer la gestion des clés secrètes et des mots de passe administratifs ([699345f](https://github.com/cyr-ius/wireguard-ui/commit/699345f4b8c5cf5b5816faa7d07ee1f108382d4b))
* **docs:** make English the default site/README language, add French translations ([49b9a6c](https://github.com/cyr-ius/wireguard-ui/commit/49b9a6c2508fe138fef8024c28aca051f14d5fe9))
* **frontend:** force initial server/endpoint setup on first admin login ([2d31542](https://github.com/cyr-ius/wireguard-ui/commit/2d315426cc5738ab698a6691b0ac1e9031b6b74d))
* **server:** add loading feedback for service control buttons ([be23552](https://github.com/cyr-ius/wireguard-ui/commit/be23552481f492efc053f15b8b09b6722f49a7b2))


### Bug Fixes

* add alembic installation to Dockerfile dependencies ([c0495bb](https://github.com/cyr-ius/wireguard-ui/commit/c0495bbed91d3c9c8ea9ff724e58598c404ce2e9))
* corriger l'importation de FormFieldBinding et mettre à jour les validations dans les composants de formulaire ([783e566](https://github.com/cyr-ius/wireguard-ui/commit/783e566ea96d4c959e1fc65b8872fe8264046b09))
* **devcontainer:** update Node.js feature version to 2.1.1 ([b424f44](https://github.com/cyr-ius/wireguard-ui/commit/b424f448f8fd9b7ce89983f543da56e49b7f3f2d))
* **docs:** Add first start explication ([7694f32](https://github.com/cyr-ius/wireguard-ui/commit/7694f3294ecfde5402056878ca3152b7bef50a83))
* **docs:** Add requirements file ([90d9e1c](https://github.com/cyr-ius/wireguard-ui/commit/90d9e1c983eb5ac39bfcede2ee7597a5f6f3fe17))
* **docs:** Clarify SECRET_KEY is optional, not required to start ([cdfaf96](https://github.com/cyr-ius/wireguard-ui/commit/cdfaf960483089d76051aa99537fd4cef9a3f8f9))
* **docs:** Summarize ([beabe6f](https://github.com/cyr-ius/wireguard-ui/commit/beabe6feb1d6f78603308eadd5421a2ff68d9292))
* **oidc:** forbid credential and profile changes for OIDC accounts ([4398983](https://github.com/cyr-ius/wireguard-ui/commit/4398983e5354190b389a6acacdd22bfe2776fa94))
* **oidc:** prevent OIDC/local account collision and usurpation ([4e79150](https://github.com/cyr-ius/wireguard-ui/commit/4e7915073256aaab2bdfa69e365e930e98bebf41))
* reduce retry attempts for Alembic migrations ([ada9924](https://github.com/cyr-ius/wireguard-ui/commit/ada992491b7b52796b14a758e724d353335163fd))
* sécuriser les cookies et simplifier la configuration des paramètres ([a711b29](https://github.com/cyr-ius/wireguard-ui/commit/a711b292160bfb607beafd0e8b95583fec847cbf))
* supprimer le mot de passe admin par défaut et générer un mot de passe lors de la création du compte admin ([590a876](https://github.com/cyr-ius/wireguard-ui/commit/590a876145397f53c99877a2c24e93cb92fa4a94))
* **theme:** remplacer couleurs light hardcodées par variables CSS ([9647b07](https://github.com/cyr-ius/wireguard-ui/commit/9647b074069b15b1e6aa4660dd36deee7bace53e))
* update Docker configuration for persistence and ports ([06930e7](https://github.com/cyr-ius/wireguard-ui/commit/06930e7d5b9e70a6dd83c5d3807bf85223824288))
