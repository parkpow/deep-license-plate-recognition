# Blur
View the [documentation](https://guides.platerecognizer.com/docs/blur/getting-started).

## Setup
1. Build the image
```bash
docker build --tag platerecognizer/blur .

```

2. Run Image
```
docker run --rm --net=host -t -v /tmp/test-images:/images platerecognizer/blur --images=/images --blur-url=http://localhost:5000

```
