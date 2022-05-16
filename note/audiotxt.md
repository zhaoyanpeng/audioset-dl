## Curated Audio-Text Data

To reduce file size, we split curated data into an index file (*_cap.csv) and a map file (*_map.csv).

### *_cap.csv

Since a caption can be assigned to multiple video frames, it is better to associate each video frame with a set of
caption ids rather than actual captions. For example:

```
head -n 10 IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B16_predictions_cap.csv

# outputs

["---1_cCGK4M.p0.4_01", [165818, 57538, 109699, 10446, 10447, 46004, 78425, 90234, 62011, 1596]]
["---1_cCGK4M.p0.4_02", [44000, 44002, 20963, 105606, 42599, 46184, 31056, 29008, 29011, 35934]]
["---1_cCGK4M.p0.4_03", [44000, 186690, 44002, 52518, 42599, 46184, 88747, 29008, 5522, 35934]]
["---1_cCGK4M.p0.4_04", [44000, 186690, 20963, 44002, 52518, 92870, 46184, 42599, 15312, 144988]]
["---2_BBVHAA.p0.4_01", [153889, 19394, 40454, 7494, 83434, 7502, 126418, 160124, 177497, 10620]]
["---2_BBVHAA.p0.4_02", [153889, 19394, 217894, 40454, 34830, 347313, 126418, 160124, 116027, 10620]]
["---2_BBVHAA.p0.4_03", [158752, 19394, 217894, 40454, 7502, 34830, 126418, 160124, 116027, 10620]]
["---2_BBVHAA.p0.4_04", [19394, 217894, 40454, 68876, 7502, 347313, 126418, 160124, 22970, 10620]]
["---B_v8ZoBY.p0.4_01", [3753, 266, 3164, 272, 412, 827, 1052, 413, 1054, 1055]]
["---B_v8ZoBY.p0.4_02", [7841, 3753, 3754, 7243, 3755, 112973, 3756, 6898, 13115, 2366]]
```

Each line is of type `LIST[STR, LIST]`, which can be parsed by `json.loads(line)`. `STR` is composed of
`[YOUTUBE_ID].p0.[NUM_TOTAL_FRAME].[FRAME_INDEX]` (`p0` is a special key indicating the $k$-th positive video clip where $k=0$). `LIST` contains a list of ten caption ids.


### *_map.csv

All curated captions come from a finite set of captions, we index each caption with a unique key. For example:

```
head -n 10 IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B16_predictions_map.csv

# outputs

[0, "Man doing a skateboard trick in front of a crowd."]
[1, "a man skating on a wire and people watching"]
[2, "A man loses his skateboard at the top of a ramp while a crowd watches."]
[3, "Man on skateboard in air skating on ramp near people."]
[4, "A man doing a skateboard jump trick in front of spectators."]
[5, "A man wearing a orange shirt is throwing a frisbee"]
[6, "A man is doing a skateboard trick in front of a crowd."]
[7, "A man is skateboarding on the ramp in front of a crowd."]
[8, "Crowd watches while guy slides down railing on skateboard"]
[9, "Man jumps skateboard over a stack of wood while people watch"]
```

Similarly to the index file, each line is of type `LIST[INT, STR]` and can be parsed by `json.loads(line)`.

## Download

We release caption data curated by ViT-B32. This is the data we used in our paper. We also release curated data by ViT-B16 for interested users to explore. 

- Curated by ViT-B16: Audio Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_audio_captions_train_caption_features~ViT-B16_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_audio_captions_train_caption_features~ViT-B16_predictions_map.csv)), Image Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B16_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B16_predictions_map.csv)), Free Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_round1_combined_caption_features~ViT-B16_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B16~widescreen_CAPTION_round1_combined_caption_features~ViT-B16_predictions_map.csv)).

- Curated by ViT-B32: Audio Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_audio_captions_train_caption_features~ViT-B32_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_audio_captions_train_caption_features~ViT-B32_predictions_map.csv)), Image Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B32_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_all_coco_captions_caption_features~ViT-B32_predictions_map.csv)), Free Captions ([CAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_round1_combined_caption_features~ViT-B32_predictions_cap.csv), [MAP](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/IMAGE_frame_image_features~ViT-B32~widescreen_CAPTION_round1_combined_caption_features~ViT-B32_predictions_map.csv)).

We further gather the captions of video frames that correspond to the same vidio clip. The resulting set of captions are used as the captions of the corresponding video/audio clip. We provide json files of type `DICT[STR, LIST]` (i.e., `{YOUTUBE_ID: LIST_OF_CAPTION_IDS}`). Pre-embedded captions of type `NPZ`  are also available to download (embedded by CLIP text encoder) :

- Curated by ViT-B16: Audio Captions ([DICT](), [NPZ]()), Image Captions  ([DICT](), [NPZ]()), Free Captions  ([DICT](), [NPZ]()); [ALL IN ONE](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/vit_b16.tar.gz).

- Curated by ViT-B32: Audio Captions ([DICT](), [NPZ]()), Image Captions  ([DICT](), [NPZ]()), Free Captions  ([DICT](), [NPZ]()); [ALL IN ONE](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/curated/vit_b32.tar.gz).
