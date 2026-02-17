tåg.html: build main.js
	./build $@

.PHONY: upload
upload: tåg.html
	aws s3 cp --acl=public-read $< s3://rootmos-www/mdu/$<

.PHONY: clean
clean:
	rm -f tåg.html
