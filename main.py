
import csv
import math

# Lớp biểu diễn các điểm 3D
class Point3D:
    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def distance_to(self, other_point):
        return math.sqrt(
            (self.x - other_point.x)**2 +
            (self.y - other_point.y)**2 +
            (self.z - other_point.z)**2
        )

# Lớp biểu diễn một điểm pose (ví dụ: LShoulder, RElbow) 
class PosePoint:
    def __init__(self, name, x, y, z):
        self.name = name
        self.coordinates = Point3D(x, y, z)

#Lớp biểu diễn một đoạn xương (Bone Segment) 
class BoneSegment:
    def __init__(self, name, start_point: PosePoint, end_point: PosePoint):
        self.name = name
        self.start_point = start_point
        self.end_point = end_point
        self.length = self.calculate_length()

    def calculate_length(self):
        if self.start_point and self.end_point:
            return self.start_point.coordinates.distance_to(self.end_point.coordinates)
        return 0.0

#Lớp chứa dữ liệu khung xương cho một frame cụ thể

class SkeletonData:
    def __init__(self, frame_id, pose_data):
        self.frame_id = int(frame_id)
        self.pose_points = {}
        for name, coords in pose_data.items():
            if coords: 
                self.pose_points[name] = PosePoint(name, *coords)
            else:
                self.pose_points[name] = None 
        
        self.bone_segments = {} 
        self.estimated_height = 0.0
        self.calculate_bone_segments()
        self.estimate_height()

    def calculate_bone_segments(self):
        bone_definitions = {
            "PELVIS_TO_SPINE1": ("PELVIS", "SPINE1"),
            "SPINE1_TO_SPINE2": ("SPINE1", "SPINE2"),
            "SPINE2_TO_SPINE3": ("SPINE2", "SPINE3"),
            "SPINE3_TO_NECK": ("SPINE3", "NECK"),
            "NECK_TO_HEAD": ("NECK", "HEAD"),

            "LEFT_COLLAR_TO_LEFT_SHOULDER": ("LEFT_COLLAR", "LEFT_SHOULDER"),
            "LEFT_SHOULDER_TO_LEFT_ELBOW": ("LEFT_SHOULDER", "LEFT_ELBOW"),
            "LEFT_ELBOW_TO_LEFT_WRIST": ("LEFT_ELBOW", "LEFT_WRIST"),
            
            "RIGHT_COLLAR_TO_RIGHT_SHOULDER": ("RIGHT_COLLAR", "RIGHT_SHOULDER"),
            "RIGHT_SHOULDER_TO_RIGHT_ELBOW": ("RIGHT_SHOULDER", "RIGHT_ELBOW"),
            "RIGHT_ELBOW_TO_RIGHT_WRIST": ("RIGHT_ELBOW", "RIGHT_WRIST"),

            "LEFT_HIP_TO_LEFT_KNEE": ("LEFT_HIP", "LEFT_KNEE"),
            "LEFT_KNEE_TO_LEFT_ANKLE": ("LEFT_KNEE", "LEFT_ANKLE"),
            "LEFT_ANKLE_TO_LEFT_FOOT": ("LEFT_ANKLE", "LEFT_FOOT"), 

            "RIGHT_HIP_TO_RIGHT_KNEE": ("RIGHT_HIP", "RIGHT_KNEE"),
            "RIGHT_KNEE_TO_RIGHT_ANKLE": ("RIGHT_KNEE", "RIGHT_ANKLE"),
            "RIGHT_ANKLE_TO_RIGHT_FOOT": ("RIGHT_ANKLE", "RIGHT_FOOT"), 

            "LEFT_HIP_TO_RIGHT_HIP": ("LEFT_HIP", "RIGHT_HIP"),
            "LEFT_SHOULDER_TO_RIGHT_SHOULDER": ("LEFT_SHOULDER", "RIGHT_SHOULDER"), 
            "PELVIS_TO_LEFT_HIP": ("PELVIS", "LEFT_HIP"), 
            "PELVIS_TO_RIGHT_HIP": ("PELVIS", "RIGHT_HIP"), 
            
        }

        for bone_name, (start_name, end_name) in bone_definitions.items():
            start_point = self.pose_points.get(start_name)
            end_point = self.pose_points.get(end_name)
            if start_point and end_point: 
                self.bone_segments[bone_name] = BoneSegment(bone_name, start_point, end_point)

    def estimate_height(self):
        torso_length = 0
        if self.bone_segments.get("PELVIS_TO_SPINE1") and \
           self.bone_segments.get("SPINE1_TO_SPINE2") and \
           self.bone_segments.get("SPINE2_TO_SPINE3") and \
           self.bone_segments.get("SPINE3_TO_NECK") and \
           self.bone_segments.get("NECK_TO_HEAD"):
            torso_length = (self.bone_segments["PELVIS_TO_SPINE1"].length +
                            self.bone_segments["SPINE1_TO_SPINE2"].length +
                            self.bone_segments["SPINE2_TO_SPINE3"].length +
                            self.bone_segments["SPINE3_TO_NECK"].length +
                            self.bone_segments["NECK_TO_HEAD"].length)
        elif self.pose_points.get("PELVIS") and self.pose_points.get("HEAD"):
            torso_length = self.pose_points["PELVIS"].coordinates.distance_to(self.pose_points["HEAD"].coordinates)
        
        avg_leg_length = 0
        left_leg_segments = ["LEFT_HIP_TO_LEFT_KNEE", "LEFT_KNEE_TO_LEFT_ANKLE", "LEFT_ANKLE_TO_LEFT_FOOT"]
        right_leg_segments = ["RIGHT_HIP_TO_RIGHT_KNEE", "RIGHT_KNEE_TO_RIGHT_ANKLE", "RIGHT_ANKLE_TO_RIGHT_FOOT"]
        
        left_leg_total_length = sum(self.bone_segments[s].length for s in left_leg_segments if s in self.bone_segments)
        right_leg_total_length = sum(self.bone_segments[s].length for s in right_leg_segments if s in self.bone_segments)

        if left_leg_total_length > 0 and right_leg_total_length > 0:
            avg_leg_length = (left_leg_total_length + right_leg_total_length) / 2
        elif left_leg_total_length > 0:
            avg_leg_length = left_leg_total_length
        elif right_leg_total_length > 0:
            avg_leg_length = right_leg_total_length
        
        # Tổng chiều cao
        if torso_length > 0 and avg_leg_length > 0:
            self.estimated_height = torso_length + avg_leg_length
        elif self.pose_points.get("HEAD") and self.pose_points.get("LEFT_FOOT"):
            # Một ước lượng thay thế nếu có điểm HEAD và FOOT
            self.estimated_height = self.pose_points["HEAD"].coordinates.distance_to(self.pose_points["LEFT_FOOT"].coordinates)
        elif self.pose_points.get("HEAD") and self.pose_points.get("RIGHT_FOOT"):
            self.estimated_height = self.pose_points["HEAD"].coordinates.distance_to(self.pose_points["RIGHT_FOOT"].coordinates)
# Lớp xử lý file csv
class CSVReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_data(self):
        all_skeleton_data = []
        try:
            with open(self.file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  
                
                col_map = {col: i for i, col in enumerate(header)}
                
                pose_point_names = sorted(list(set(col.rsplit('_', 1)[0] for col in header if '_' in col and col != 'frame')))
                
                for row in reader:
                    frame_id = row[col_map['frame']]
                    current_pose_data = {}
                    for pose_name in pose_point_names:
                        x_col = f"{pose_name}_X"
                        y_col = f"{pose_name}_Y"
                        z_col = f"{pose_name}_Z"
                        
                        if x_col in col_map and y_col in col_map and z_col in col_map:
                            try:
                                x = float(row[col_map[x_col]])
                                y = float(row[col_map[y_col]])
                                z = float(row[col_map[z_col]])
                                current_pose_data[pose_name] = (x, y, z)
                            except ValueError:
                                current_pose_data[pose_name] = None
                        else:
                            current_pose_data[pose_name] = None 
                    
                    all_skeleton_data.append(SkeletonData(frame_id, current_pose_data))
            return all_skeleton_data
        except FileNotFoundError:
            print(f"Error : File not found {self.file_path}")
            return []
        except Exception as e:
            print(f"Error while reading file: {e}")
            return []

# Lớp kiểm tra dữ liệu khung xương 
class SkeletonValidator:
    def __init__(self):
        self.standard_bone_ratios = {
                "Shoulder Elbow": 0.18,  
                "Elbow Wrist": 0.14,    
                "Hip Knee": 0.24,        
                 "Knee Ankle": 0.22,      
                 "Neck Head": 0.12,      
                 "Torso": 0.25, 
        }

        # Các cặp đoạn xương đối xứng
        self.symmetric_bone_pairs = {
                ("LEFT_SHOULDER_TO_LEFT_ELBOW", "RIGHT_SHOULDER_TO_RIGHT_ELBOW"),
                ("LEFT_ELBOW_TO_LEFT_WRIST", "RIGHT_ELBOW_TO_RIGHT_WRIST"),
                ("LEFT_HIP_TO_LEFT_KNEE", "RIGHT_HIP_TO_RIGHT_KNEE"),
                ("LEFT_KNEE_TO_LEFT_ANKLE", "RIGHT_KNEE_TO_RIGHT_ANKLE"),
                ("LEFT_ANKLE_TO_LEFT_FOOT", "RIGHT_ANKLE_TO_RIGHT_FOOT"),
                ("LEFT_COLLAR_TO_LEFT_SHOULDER", "RIGHT_COLLAR_TO_RIGHT_SHOULDER"),
                ("LEFT_HIP_TO_RIGHT_HIP", "RIGHT_HIP_TO_LEFT_HIP"),
             }
        
        self.intra_segment_ratios = {

            "Arm_Ratio": ("Shoulder Elbow", "Elbow Wrist", 1.28),
            "Leg_Ratio": ("Hip Knee", "Knee Ankle", 1.09), 

        }
        # Sai số cho phép
        self.ratio_tolerance = 0.20 
        self.symmetry_tolerance = 0.10 

    def print_standard_ratios(self):
        for name, ratio in self.standard_bone_ratios.items():
            print(f"{name} {ratio*100:.0f}%")

    def validate_ratio(self, skeleton_data: SkeletonData):
        errors = []
        if skeleton_data.estimated_height == 0:
            return errors 
        
        for ratio_name, (bone1_name, bone2_name, expected_ratio) in self.intra_segment_ratios.items():
                       
            # Kiểm tra cho bên trái
            b1_left_name = "L" + bone1_name.replace(" ", "_TO_")
            b2_left_name = "L" + bone2_name.replace(" ", "_TO_")
            
            b1_left = skeleton_data.bone_segments.get(b1_left_name)
            b2_left = skeleton_data.bone_segments.get(b2_left_name)

            if b1_left and b2_left and b2_left.length > 0:
                actual_ratio_left = b1_left.length / b2_left.length
                if abs(actual_ratio_left - expected_ratio) / expected_ratio > self.ratio_tolerance:
                    errors.append(f"L{bone1_name.replace(' ', '_TO_')} : L{bone2_name.replace(' ', '_TO_')} {actual_ratio_left:.1f} : 1 (WRONG - Invalidate ratio)")
            
            # Kiểm tra cho bên phải
            b1_right_name = "R" + bone1_name.replace(" ", "_TO_")
            b2_right_name = "R" + bone2_name.replace(" ", "_TO_")

            b1_right = skeleton_data.bone_segments.get(b1_right_name)
            b2_right = skeleton_data.bone_segments.get(b2_right_name)

            if b1_right and b2_right and b2_right.length > 0:
                actual_ratio_right = b1_right.length / b2_right.length
                if abs(actual_ratio_right - expected_ratio) / expected_ratio > self.ratio_tolerance:
                    errors.append(f"R{bone1_name.replace(' ', '_TO_')} : R{bone2_name.replace(' ', '_TO_')} {actual_ratio_right:.1f} : 1 (WRONG - Invalidate ratio)")

        return errors

    def validate_symmetry(self, skeleton_data: SkeletonData):
        errors = []
        for left_bone_name, right_bone_name in self.symmetric_bone_pairs:
            left_bone = skeleton_data.bone_segments.get(left_bone_name)
            right_bone = skeleton_data.bone_segments.get(right_bone_name)

            if left_bone and right_bone:
                if left_bone.length > 0 or right_bone.length > 0: 
                    max_len = max(left_bone.length, right_bone.length)
                    if max_len > 0:
                        percentage_diff = abs(left_bone.length - right_bone.length) / max_len
                        if percentage_diff > self.symmetry_tolerance:
                            errors.append(f"{left_bone_name} # {right_bone_name} (Invalidate Symmetric match: {left_bone.length:.2f} vs {right_bone.length:.2f})")
        return errors

def main():
    file_name = "test.csv"
    reader = CSVReader(file_name)
    all_skeleton_data = reader.read_data()

    if not all_skeleton_data:
        print("Data not found or eror.")
        return

    validator = SkeletonValidator()
    validator.print_standard_ratios()

    has_errors = False
    
    for skeleton_data in all_skeleton_data:
        ratio_errors = validator.validate_ratio(skeleton_data)
        symmetry_errors = validator.validate_symmetry(skeleton_data)

        if ratio_errors or symmetry_errors:
            has_errors = True
            print(f"\n--- Error in {skeleton_data.frame_id} ---")
            for error in ratio_errors:
                print(error)
            for error in symmetry_errors:
                print(error)
    
    if not has_errors:
        print("\nCLEAR")

if __name__ == "__main__":
    main()
