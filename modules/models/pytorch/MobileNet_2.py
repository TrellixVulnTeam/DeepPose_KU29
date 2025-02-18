# -*- coding: utf-8 -*-

import torch.nn as nn
import torch.nn.functional as F

class MobileNet_2(nn.Module):
    def __init__(self):
        super(MobileNet_2, self).__init__()
        self.col = 14
        self.Nj = 14

        def conv_bn(inp, oup, stride):
            return nn.Sequential(
                nn.Conv2d(inp, oup, 3, stride, 1, bias=False),
                nn.BatchNorm2d(oup),
                nn.ReLU(inplace=True)
            )

        def conv_dw(inp, oup, stride):
            return nn.Sequential(
                nn.Conv2d(inp, inp, 3, stride, 1, groups=inp, bias=False),
                nn.BatchNorm2d(inp),
                nn.ReLU(inplace=True),
    
                nn.Conv2d(inp, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
                nn.ReLU(inplace=True),
            )

        self.model = nn.Sequential(
            conv_bn(  3,  32, 2), 
            conv_dw( 32,  64, 1),
            conv_dw( 64, 128, 2),
            conv_dw(128, 128, 1),
            conv_dw(128, 256, 2),
            conv_dw(256, 256, 1),
            conv_dw(256, 512, 2),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 1024, 1),
            conv_dw(1024, 1024, 1),
            #nn.AvgPool2d(7),
        )
        #self.fc1= nn.AvgPool2d(14)
        self.fc2 = nn.Conv2d(1024, self.Nj*3, 1)
        #self.fc2 = nn.Linear(1024, 14)

    def forward(self, x):
        x = self.model(x)
        x = self.fc2(x)
        #x = x.view(-1, 1024)

        return x
