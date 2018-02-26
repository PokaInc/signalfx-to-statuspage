STACK_NAME=signalfx-to-statuspage-integration
CONFIG_FILE = config.ini
SOURCE_TEMPLATE_PATH = signalfx_to_statuspage_integration.yml
GENERATED_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(SOURCE_TEMPLATE_PATH)
BUCKET_NAME=$(STACK_NAME)-`aws sts get-caller-identity --output text --query 'Account'`-`aws configure get region`

check-bucket:
	@aws s3api head-bucket --bucket $(BUCKET_NAME) &> /dev/null || aws s3 mb s3://$(BUCKET_NAME)

package: check-bucket
	@./package_lambda.sh
	@aws cloudformation package --template-file $(SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/$(SOURCE_TEMPLATE_PATH).yml --output-template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH)

deploy: package
	@test -f $(CONFIG_FILE) || (echo $(CONFIG_FILE) must exist && exit 1)
	aws cloudformation deploy --template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH) --stack-name $(STACK_NAME) --capabilities CAPABILITY_IAM --parameter-overrides `(IFS=$$'\n'; echo $$(< $(CONFIG_FILE)))`
