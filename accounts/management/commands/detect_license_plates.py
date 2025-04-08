from django.core.management.base import BaseCommand
from accounts.license_detector import LicensePlateDetector
import os
import glob

class Command(BaseCommand):
    help = 'Run license plate detection using camera or from image files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            choices=['camera', 'images', 'file'],
            default='camera',
            help='Detection mode: camera, images (directory), or single file'
        )
        parser.add_argument(
            '--path',
            type=str,
            help='Path to image file or directory with images'
        )
    
    def handle(self, *args, **options):
        try:
            detector = LicensePlateDetector()
            mode = options['mode']
            
            if mode == 'camera':
                self.stdout.write('Running detection using camera...')
                try:
                    plate_text, snapshot_path = detector.detect_from_camera()
                    self.stdout.write(self.style.SUCCESS(
                        f'Detected license plate: {plate_text}, saved to {snapshot_path}'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            
            elif mode == 'file' and options['path']:
                self.stdout.write(f'Processing image file: {options["path"]}')
                try:
                    plate_text, snapshot_path = detector.detect_from_image(options['path'])
                    self.stdout.write(self.style.SUCCESS(
                        f'Detected license plate: {plate_text}, saved to {snapshot_path}'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            
            elif mode == 'images' and options['path']:
                dir_path = options['path']
                self.stdout.write(f'Processing all images in directory: {dir_path}')
                
                image_files = glob.glob(os.path.join(dir_path, '*.jpg')) + \
                            glob.glob(os.path.join(dir_path, '*.jpeg')) + \
                            glob.glob(os.path.join(dir_path, '*.png'))
                
                for img_file in image_files:
                    self.stdout.write(f'Processing: {img_file}')
                    try:
                        plate_text, snapshot_path = detector.detect_from_image(img_file)
                        self.stdout.write(
                            f'Detected license plate: {plate_text}, saved to {snapshot_path}'
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing {img_file}: {str(e)}'))
            
            else:
                self.stdout.write(self.style.ERROR('Invalid command options'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Setup error: {str(e)}'))