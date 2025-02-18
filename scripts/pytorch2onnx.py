# -*- coding: utf-8 -*-

import argparse
from torch.autograd import Variable
import torch.onnx
import torchvision.models as models
import onnx
import numpy as np
#from keras.models import load_model
import torch.nn.parallel
import torch.backends.cudnn as cudnn

import sys
sys.path.append("./")
from onnx_coreml.converter import convert
#from pytorch2keras.converter import pytorch_to_keras
from modules.errors import FileNotFoundError, GPUNotFoundError, UnknownOptimizationMethodError, NotSupportedError
from modules.models.pytorch import AlexNet, VGG19Net, Inceptionv3, Resnet, MobileNet, MobileNetV2, MobileNet_, MobileNet_2, MobileNet_3, MobileNet_4, MobileNet___, MnasNet, MnasNet_,MnasNet56_,MnasNet16_,MobileNet16_,MobileNet14_,MobileNet14_4,MobileNet14_5,MobileNet224HM, MobileNetCoco14_5,MobileNet3D,MobileNet3D2,MnasNet3D
#from coremltools.converters.keras import convert
from modules.dataset_indexing.pytorch import PoseDataset, Crop, RandomNoise, Scale
from torchvision import transforms
from PIL import Image
from onnx_tf.backend import prepare

'''
再帰的に呼び出してpruningを行う
'''
def pruning(module, threshold):
    print(module)

    if module != None:
        if isinstance(module, torch.nn.Sequential):
            for child in module.children():
                pruning(child, threshold)

        if isinstance(module, torch.nn.Conv2d):
            old_weights = module.weight.data.cpu().numpy()
            new_weights = (np.absolute(old_weights) > threshold) * old_weights
            module.weight.data = torch.from_numpy(new_weights)

        if isinstance(module, torch.nn.BatchNorm2d):
            #module.track_running_stats = False
            print(module.weight)
            module.eval()
            module.weight.requires_grad = False
            module.bias.requires_grad = False

            '''
            module.weight is gamma = 1
            running_mean is mean = 0
            running_var is variance = 1
            bias is beta
            '''
            #module.weight.data = torch.from_numpy(np.ones_like(module.weight.data)) 
            #module.running_mean.data = torch.from_numpy(np.zeros_like(module.running_mean.data)) 
            #module.running_var.data = torch.from_numpy(np.ones_like(module.running_var.data)) 


print('ArgumentParser')
parser = argparse.ArgumentParser(description='Convert PyTorch model to CoreML')
parser.add_argument('--input', '-i', required=True, type=str)
parser.add_argument('--output', '-o', required=True, type=str)
parser.add_argument('--NN', '-n', required=True, type=str)
parser.add_argument('--onnx_output', required=True, type=str)
parser.add_argument('--image_size', required=True, type=int)
parser.add_argument('--is_checkpoint', required=True, type=int)
parser.add_argument('--onedrive', required=False, type=str)
parser.add_argument('--NJ', required=True, type=int)
parser.add_argument('--Col', required=True, type=int)

args = parser.parse_args()

print('Set up model')
if args.NN == "MobileNet":
    model = MobileNet( )
elif args.NN == "MobileNet_":
    model = MobileNet_( )
elif args.NN == "MobileNet___":
    model = MobileNet___( )
elif args.NN == "MobileNet_3":
    model = MobileNet_3( )
elif args.NN == "MnasNet":
    model = MnasNet( )
elif args.NN == "MnasNet_":
    model = MnasNet_( )
elif args.NN == "MnasNet56_":
    model = MnasNet56_( )
elif args.NN == "MnasNet16_":
    model = MnasNet16_( )
elif args.NN == "MobileNet16_":
    model = MobileNet16_( )
else:
    model = eval(args.NN)()

#elif args.NN == "MobileNet162_":
#    model = MobileNet162_( )

cudnn.benchmark = True
torch.backends.cudnn.deterministic = False
torch.backends.cudnn.enabled = True

print('load model')

if args.is_checkpoint == 1:
    checkpoint = torch.load(args.input)
    state_dict = checkpoint['state_dict']
    model.load_state_dict(state_dict)
    optimizer_state_dict = checkpoint['optimizer']
else:
    model.load_state_dict(torch.load(args.input))

'''
# create new OrderedDict that does not contain `module.`
from collections import OrderedDict
new_state_dict = OrderedDict()
for k, v in state_dict.items():
    name = k[7:] # remove `module.`
    new_state_dict[name] = v
# load params
model.load_state_dict(new_state_dict)
'''
#model = model.cpu()
model.eval()

# export to ONNF
img_path = "im07276.jpg"
img = Image.open(img_path).convert('RGB')
img = img.resize((args.image_size, args.image_size))
arr = np.asarray(img, dtype=np.float32)[np.newaxis, :, :, :]
dummy_input = Variable(torch.from_numpy(arr.transpose(0, 3, 1, 2)/255.))
#dummy_input = Variable(torch.randn(1, 3, args.image_size, args.image_size))
################
heatmap = model.forward(dummy_input)

'''
##pruning##
all_weights = []
for p in model.parameters():
    if len(p.data.size()) != 1:
        all_weights += list(p.cpu().data.abs().numpy().flatten())
threshold = np.percentile(np.array(all_weights), 10.)

pruning(model.model, threshold)
'''

model.eval()
#model.cuda()

##################
print('converting to ONNX')
torch.onnx.export(model, dummy_input, args.onnx_output)
onnx_model = onnx.load(args.onnx_output)

onnx.checker.check_model(onnx_model)

#scale = 1./ (args.image_size - 1.)
scale = 1./ 255.
print('converting coreml model')
mlmodel = convert(
        onnx_model, 
        preprocessing_args={'is_bgr':True, 'red_bias':0., 'green_bias':0., 'blue_bias':0., 'image_scale':scale},
        image_input_names='0')
mlmodel.save(args.output)

if args.onedrive != "":
    print('save  onedrive')
    mlmodel.save(args.onedrive)

print('Finish convert')


