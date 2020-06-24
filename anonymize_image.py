"""Script with functions to anonymize images"""

import cv2
from PIL import Image
import numpy as np
import torch
import torchvision.models
import torchvision.transforms as T

ANON_COLOR = 100

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

classes = ['__background__', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
           'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike',
           'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']

seg_model = torchvision.models.segmentation.deeplabv3_resnet101(pretrained=True).eval().to(device)

# From https://www.learnopencv.com/pytorch-for-beginners-semantic-segmentation-using-torchvision/
trf = T.Compose([T.Resize((500,500)),#256),
                 #T.CenterCrop(224),
                 T.ToTensor(),
                 T.Normalize(mean = [0.485, 0.456, 0.406],
                             std = [0.229, 0.224, 0.225])])

def anonymize_image(img):
    """
    Anonymize a given image by replacing identifying personal information with grey pixels
    
    args:
        img (np.array[w, h, channels]) : cv2 BGR image
    
    return:
        np.array[w, h, channels] : anonymized RGB image
    """
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    
    inp = trf(im_pil).unsqueeze(0)
    out = seg_model(inp.to(device))['out']
    seg = torch.argmax(out.squeeze(), dim=0).detach().cpu().numpy()
    
    person_mask = seg == classes.index('person')
    
    img = np.array(img)
    
    person_mask = person_mask[np.newaxis]
    person_mask = np.transpose(person_mask, (1,2,0))
    person_mask = np.tile(person_mask, (1,1,3))
    person_mask = person_mask.astype(np.float64)
    person_mask = cv2.resize(person_mask, (img.shape[1], img.shape[0]), interpolation = cv2.INTER_AREA)
    person_mask[person_mask > 0.1] = 1 # smooth after the resize
    
    anon_img = img.copy()
    anon_img[person_mask == 1] = ANON_COLOR

    return anon_img[:,:,::-1]