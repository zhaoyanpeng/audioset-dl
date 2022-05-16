## Notes on AudioSet Index Files

### Convert AudioSet into Index Files

- `src_train_segments.csv` combines the unbalanced and balanced training sets: the splitting line number is 1715367.

- `src_unbalanced_train_segments.csv` is a copy of `src_full_unbalanced_train_segments.csv`.

- `src_unbalanced_train_segments_weight.csv` contains a weight of type `FLOAT` for each sample in `src_unbalanced_train_segments.csv`, note that there is line-to-line mapping between the two files. There weights are computed as the inverse of audio class frequencies.

- `src_audiocaps_*` are AudioCaps in our pre-training-data format, e.g.,

```
head -n 1 src_audiocaps_val.csv

# outputs

{
	"dir": "all_1960000_1995000", 
	"aclip": ["p0.mp3"], 
	"frame": ["p0.4_01.jpg", "p0.4_02.jpg", "p0.4_03.jpg", "p0.4_04.jpg"], 
	"aclip_128": "p0.npz", 
	"frame_224": "p0.npz", 
	"id": "vfY_TJq7n_U", 
	"bos": "130.000", 
	"eos": "140.000", 
	"labels": ["/m/09ddx", "/m/09x0r", "/m/0jbk"], 
	"captions": ["Rustling occurs, ducks quack and water splashes, followed by an adult female and adult male speaking and duck calls being blown", "Ducks quack as a man speaks and makes a duck sound", "Birds chirp and ducks squawk while a man and woman speak", "Birds chirp and ducks quack before a man speaks", "Ducks quack and a man speaks"]
}
```
where 
- **dir**: sub directory which contains the current audio clip. To make parallel data processing easier, we divide AudioSet audio into consecutive chunks (aka **dir**), e.g., all_0_35000, all_35000_70000, ..., all_2030000_2065000, all_2065000_2100000.
- **aclip**: audio clip suffix, `p0` indicates the gold clip, you may see `n[\d]` which indicates negative clips croped from the video before or after the gold clip.
- **frame**: video frame suffix, `p0.[\d]_[\d].jpg` where the first number is the total number of video frames; the second number is the frame index.
- **aclip_128**: pre-encoded audio clip (discarded).
- **frame_224**: pre-encoded video frames (discarded).
- **id**: youtube id.
- **bos**: start time of the gold clip.
- **eos**: ending time of the gold clip.
- **labels**: a list of ids which rely on `ontology.json` to parse.
-  **captions**: only appear in audio captioning datasets.

See [__getitem__](https://github.com/zhaoyanpeng/vipant/blob/2cab22a00b905f4b9d858b3e88395e5df54e7fa1/cvap/data/audioset_clf.py#L68) as to parse each input sample.

### Balance Unbalanced Training data

We hypothesize that augmenting the balanced training set would be more data-efficient than using the whole training set.

For each sample in the balanced training set we find the topk (100 / 512) most similar samples from the unbalanced training set. In other words, we use each sample in the balanced training set as the seed and run $k$-nn to build a sample cluster.

We use a VA [pre-trained model](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/model/01FFQTZK9YBPRDQHHR6157AGBR/00071478.pth) to do this job and take the cosine distance as the similarity measure. 

## Download

- AudioCaps ([train](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_audiocaps_train.csv), [eval](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_audiocaps_val.csv), [test](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_audiocaps_test.csv)).
- AudioSet ([balanced train](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_full_balanced_train_segments.csv), [unbalanced train](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_full_unbalanced_train_segments.csv), [weight of unbalanced train](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_unbalanced_train_segments_weight.csv), [full train](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_train_segments.csv), [eval](https://storage.googleapis.com/ai2-mosaic-public/projects/vipant/data/audioset/src_full_eval_segments.csv)).
