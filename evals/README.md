# Laboratoire d'essais ORPHEE

Ce dossier sert a conserver les essais ChatGPT de facon comparable et auditable.

## Creer un essai

Double-cliquez sur `creer_nouvel_essai.bat` a la racine du projet, puis donnez un nom court au test. Un nouveau dossier date sera cree dans `evals/runs/` a partir du modele.

Les dossiers places dans `evals/runs/` restent locaux et ne sont pas publies sur GitHub. Ils peuvent contenir des textes inedits, des conversations ou des commentaires prives.

## Contenu a conserver

Conservez les sorties exactes et non corrigees de chaque etape :

1. source, yaourt, titre et consignes;
2. Prompt 1 exactement envoye a ChatGPT;
3. reponse complete de ChatGPT au Prompt 1, incluant Handoff 1;
4. Prompt 2 exactement envoye;
5. reponse complete au Prompt 2, incluant Handoff 2;
6. Prompt 3 exactement envoye;
7. reponse complete au Prompt 3 et paroles finales;
8. rapport de l'auditeur local et prompt de correction eventuel;
9. evaluation humaine et observations.

Il est utile de conserver les reponses completes, pas seulement les handoffs. Le Handoff montre ce qui a ete transmis a l'etape suivante; la reponse complete montre comment le modele a interprete les contraintes, quels candidats il a rejetes et ou une degradation est apparue.

Ne demandez pas au modele de reveler une chaine de pensee interne. Pour l'audit, utilisez uniquement ses sorties visibles, ses justifications explicites, les handoffs et les ecarts mesurables entre les etapes.

## Demander un audit a Codex

Une fois le dossier rempli, indiquez simplement :

> Audite le dernier essai dans evals/runs. Identifie a quelle etape la qualite baisse, distingue les erreurs d'execution des faiblesses des gabarits, puis propose les modifications minimales et des tests de non-regression.

Codex pourra comparer plusieurs dossiers d'essais sans modifier les originaux.
