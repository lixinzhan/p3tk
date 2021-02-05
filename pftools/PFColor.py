from colour import Color

class PFColor(Color):
    def getRGB(self):
        return [
            int(self.get_red()*255), 
            int(self.get_green()*255), 
            int(self.get_blue()*255)
            ]