autoshutdown_v*: activate_cron.py auto_off.py autoshutdown.spec build.sh
	bash build.sh

test:
	bash test.sh

clean: autoshutdown_v*/
	rm -r build autoshutdown_v*
